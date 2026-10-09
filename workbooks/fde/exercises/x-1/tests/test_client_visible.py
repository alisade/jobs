"""Visible tests: the happy path and the breaker opening. Hidden tests cover the rest."""

from __future__ import annotations

import httpx
import pytest
from x1_support import ALLOW, PAYLOAD, make_client, routes, token_json

from risk_client import CircuitBreaker, CircuitOpen, RiskUnavailable


async def test_assess_happy_path_sends_bearer_and_json(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json("tok-1"))
    assess.respond(200, json=ALLOW)
    client = make_client(http, clock)
    assert await client.assess(PAYLOAD) == ALLOW
    sent = assess.calls.last.request
    assert sent.headers["authorization"] == "Bearer tok-1"
    assert httpx.Response(200, content=sent.content).json() == PAYLOAD


async def test_token_is_cached_across_calls(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json())
    assess.respond(200, json=ALLOW)
    client = make_client(http, clock)
    for _ in range(5):
        await client.assess(PAYLOAD)
    assert token.call_count == 1 and assess.call_count == 5


async def test_server_errors_are_risk_unavailable_not_httpx(router, http, clock):
    token, assess = routes(router)
    token.respond(200, json=token_json())
    assess.respond(503, text="upstream overloaded")
    client = make_client(http, clock)
    with pytest.raises(RiskUnavailable):
        await client.assess(PAYLOAD)


def test_breaker_opens_after_threshold_consecutive_failures(clock):
    breaker = CircuitBreaker(failure_threshold=3, reset_timeout_s=30.0, clock=clock)
    for _ in range(3):
        breaker.before_call()
        breaker.record_failure()
    assert breaker.state == "open"
    with pytest.raises(CircuitOpen):
        breaker.before_call()
