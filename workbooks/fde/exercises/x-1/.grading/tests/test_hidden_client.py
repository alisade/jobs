"""Hidden tests for fde/x-1: token lifecycle, budget, error mapping, breaker semantics."""

from __future__ import annotations

import asyncio
import base64
import time
from urllib.parse import parse_qs

import httpx
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from x1_hidden_support import (
    ALLOW,
    CLIENT_ID,
    CLIENT_SECRET,
    PAYLOAD,
    FakeClock,
    make_client,
    routes,
    token_json,
)

from risk_client import CircuitBreaker, CircuitOpen, RiskError, RiskTimeout, RiskUnavailable


async def _slow(seconds: float, response: httpx.Response):
    await asyncio.sleep(seconds)
    return response


# -- token ----------------------------------------------------------------------------


async def test_token_request_is_client_credentials_with_basic_auth(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json())
    assess.respond(200, json=ALLOW)
    await make_client(http, clock).assess(PAYLOAD)
    req = token.calls.last.request
    form = parse_qs(req.content.decode())
    assert form["grant_type"] == ["client_credentials"]
    assert form.get("scope") == ["risk.assess"]
    expected = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    assert req.headers["authorization"] == f"Basic {expected}"
    assert CLIENT_SECRET not in req.content.decode(), "the secret goes in Basic auth, not the body"


async def test_token_refreshes_early_by_the_skew(router, http, clock):
    token, assess = routes(router)
    token.side_effect = [
        httpx.Response(200, json=token_json("tok-1", 300)),
        httpx.Response(200, json=token_json("tok-2", 300)),
    ]
    assess.respond(200, json=ALLOW)
    client = make_client(http, clock, token_skew_s=30)
    await client.assess(PAYLOAD)
    clock.advance(269)
    await client.assess(PAYLOAD)
    assert token.call_count == 1, "still 31 s before expiry minus skew: reuse"
    clock.advance(2)
    await client.assess(PAYLOAD)
    assert token.call_count == 2, "inside the skew window: refresh before it expires"
    assert assess.calls.last.request.headers["authorization"] == "Bearer tok-2"


async def test_token_fetch_is_single_flight_under_concurrency(router, http, clock):
    token, assess = routes(router)
    token.side_effect = lambda request: _slow(0.05, httpx.Response(200, json=token_json()))
    assess.respond(200, json=ALLOW)
    client = make_client(http, clock, budget_s=2.0)
    results = await asyncio.gather(*(client.assess(PAYLOAD) for _ in range(50)))
    assert len(results) == 50
    assert token.call_count == 1, f"{token.call_count} token requests for one token"


async def test_401_refreshes_the_token_and_retries_once(router, http, clock):
    token, assess = routes(router)
    token.side_effect = [
        httpx.Response(200, json=token_json("revoked")),
        httpx.Response(200, json=token_json("fresh")),
    ]
    assess.side_effect = [httpx.Response(401), httpx.Response(200, json=ALLOW)]
    client = make_client(http, clock)
    assert await client.assess(PAYLOAD) == ALLOW
    assert [c.request.headers["authorization"] for c in assess.calls] == ["Bearer revoked", "Bearer fresh"]


async def test_a_second_401_is_unavailable_and_there_is_no_third_try(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json())
    assess.respond(401)
    with pytest.raises(RiskUnavailable):
        await make_client(http, clock).assess(PAYLOAD)
    assert assess.call_count == 2


async def test_token_endpoint_failure_is_unavailable(router, http, clock):
    token, _ = routes(router)
    token.respond(500)
    with pytest.raises(RiskUnavailable):
        await make_client(http, clock).assess(PAYLOAD)


# -- budget ---------------------------------------------------------------------------


async def test_slow_assess_is_a_timeout_within_the_budget(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json())
    assess.side_effect = lambda request: _slow(2.0, httpx.Response(200, json=ALLOW))
    started = time.monotonic()
    with pytest.raises(RiskTimeout):
        await make_client(http, clock, budget_s=0.1).assess(PAYLOAD)
    assert time.monotonic() - started < 0.5


async def test_budget_covers_the_token_fetch_too(router, http, clock):
    token, assess = routes(router)
    token.side_effect = lambda request: _slow(0.08, httpx.Response(200, json=token_json()))
    assess.side_effect = lambda request: _slow(0.08, httpx.Response(200, json=ALLOW))
    started = time.monotonic()
    with pytest.raises(RiskTimeout):
        await make_client(http, clock, budget_s=0.12).assess(PAYLOAD)
    assert time.monotonic() - started < 0.4


async def test_401_retry_never_runs_past_the_budget(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json())
    assess.side_effect = lambda request: _slow(0.07, httpx.Response(401))
    started = time.monotonic()
    with pytest.raises(RiskTimeout):
        await make_client(http, clock, budget_s=0.1).assess(PAYLOAD)
    assert time.monotonic() - started < 0.35


# -- error mapping ---------------------------------------------------------------------


@pytest.mark.parametrize("status", [429, 500, 502, 503])
async def test_retryable_statuses_are_unavailable(router, http, clock, status):
    token, assess = routes(router)
    token.respond(200, json=token_json())
    assess.respond(status)
    with pytest.raises(RiskUnavailable):
        await make_client(http, clock).assess(PAYLOAD)


async def test_transport_errors_never_leak_httpx(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json())
    assess.side_effect = httpx.ConnectError("connection refused")
    with pytest.raises(RiskUnavailable) as info:
        await make_client(http, clock).assess(PAYLOAD)
    assert not isinstance(info.value, httpx.HTTPError)


async def test_non_json_body_is_unavailable(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json())
    assess.respond(200, text="<html>gateway</html>")
    with pytest.raises(RiskUnavailable):
        await make_client(http, clock).assess(PAYLOAD)


async def test_a_400_is_a_risk_error_and_does_not_trip_the_breaker(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json())
    assess.respond(400, json={"error": "quantity must be positive"})
    client = make_client(http, clock)
    for _ in range(5):
        with pytest.raises(RiskError) as info:
            await client.assess(PAYLOAD)
        assert not isinstance(info.value, RiskUnavailable)
    assert client.breaker.state == "closed"


# -- breaker through the client ---------------------------------------------------------


async def test_open_breaker_makes_no_network_call(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json())
    assess.respond(503)
    client = make_client(http, clock)
    for _ in range(3):
        with pytest.raises(RiskUnavailable):
            await client.assess(PAYLOAD)
    calls = assess.call_count
    with pytest.raises(CircuitOpen):
        await client.assess(PAYLOAD)
    assert assess.call_count == calls


async def test_timeouts_count_as_breaker_failures(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json())
    assess.side_effect = lambda request: _slow(1.0, httpx.Response(200, json=ALLOW))
    client = make_client(http, clock, budget_s=0.03)
    for _ in range(3):
        with pytest.raises(RiskTimeout):
            await client.assess(PAYLOAD)
    assert client.breaker.state == "open"


async def test_half_open_trial_success_closes_and_failure_reopens(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json(expires_in=3600))
    assess.side_effect = [httpx.Response(503)] * 3 + [httpx.Response(503), httpx.Response(200, json=ALLOW)]
    client = make_client(http, clock)
    for _ in range(3):
        with pytest.raises(RiskUnavailable):
            await client.assess(PAYLOAD)
    clock.advance(30)
    assert client.breaker.state == "half_open"
    with pytest.raises(RiskUnavailable):
        await client.assess(PAYLOAD)  # the trial fails
    assert client.breaker.state == "open", "a failed trial re-opens with a fresh cool-down"
    clock.advance(29)
    with pytest.raises(CircuitOpen):
        await client.assess(PAYLOAD)
    clock.advance(1)
    assert await client.assess(PAYLOAD) == ALLOW
    assert client.breaker.state == "closed"


async def test_half_open_lets_exactly_one_trial_through(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json(expires_in=3600))
    breaker = CircuitBreaker(failure_threshold=1, reset_timeout_s=10, clock=clock)
    client = make_client(http, clock, breaker=breaker, budget_s=2.0)
    assess.respond(503)
    with pytest.raises(RiskUnavailable):
        await client.assess(PAYLOAD)
    clock.advance(10)
    assess.side_effect = lambda request: _slow(0.05, httpx.Response(200, json=ALLOW))
    before = assess.call_count
    results = await asyncio.gather(*(client.assess(PAYLOAD) for _ in range(10)), return_exceptions=True)
    assert sum(1 for r in results if r == ALLOW) == 1
    assert sum(1 for r in results if isinstance(r, CircuitOpen)) == 9
    assert assess.call_count - before == 1


async def test_a_cancelled_trial_does_not_wedge_the_breaker(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json(expires_in=3600))
    breaker = CircuitBreaker(failure_threshold=1, reset_timeout_s=10, clock=clock)
    client = make_client(http, clock, breaker=breaker, budget_s=5.0)
    assess.respond(503)
    with pytest.raises(RiskUnavailable):
        await client.assess(PAYLOAD)
    clock.advance(10)
    assess.side_effect = lambda request: _slow(2.0, httpx.Response(200, json=ALLOW))
    task = asyncio.create_task(client.assess(PAYLOAD))
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assess.side_effect = None
    assess.respond(200, json=ALLOW)
    assert await client.assess(PAYLOAD) == ALLOW, "the trial slot was released on cancel"


# -- breaker unit + property --------------------------------------------------------------


def test_breaker_validates_its_arguments(clock):
    with pytest.raises(ValueError):
        CircuitBreaker(failure_threshold=0, clock=clock)
    with pytest.raises(ValueError):
        CircuitBreaker(reset_timeout_s=0, clock=clock)


def test_success_resets_the_consecutive_count(clock):
    b = CircuitBreaker(failure_threshold=3, reset_timeout_s=5, clock=clock)
    for outcome in ["f", "f", "s", "f", "f"]:
        b.before_call()
        b.record_failure() if outcome == "f" else b.record_success()
    assert b.state == "closed" and b.consecutive_failures == 2


class _Model:
    """The reference state machine the property test compares against."""

    def __init__(self, threshold, reset):
        self.threshold, self.reset = threshold, reset
        self.failures, self.opened_at = 0, None

    def state(self, now):
        if self.opened_at is None:
            return "closed"
        return "half_open" if now - self.opened_at >= self.reset else "open"

    def call(self, now, ok):
        """Returns False when the call is rejected (CircuitOpen)."""
        if self.state(now) == "open":
            return False
        if ok:
            self.failures, self.opened_at = 0, None
        elif self.opened_at is not None:
            self.opened_at = now
        else:
            self.failures += 1
            if self.failures >= self.threshold:
                self.opened_at = now
        return True


@settings(max_examples=150, deadline=None)
@given(
    threshold=st.integers(1, 4),
    reset=st.integers(1, 20),
    steps=st.lists(st.tuples(st.sampled_from(["ok", "fail", "wait"]), st.integers(0, 15)), max_size=40),
)
def test_breaker_matches_the_reference_state_machine(threshold, reset, steps):
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=threshold, reset_timeout_s=reset, clock=clock)
    model = _Model(threshold, reset)
    for action, amount in steps:
        if action == "wait":
            clock.advance(amount)
        else:
            try:
                breaker.before_call()
                admitted = True
            except CircuitOpen:
                admitted = False
            assert admitted == model.call(clock(), action == "ok")
            if admitted:
                breaker.record_success() if action == "ok" else breaker.record_failure()
        assert breaker.state == model.state(clock())
