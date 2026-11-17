"""Hidden tests for edgefde/x-1: retries, backoff, Retry-After, budget, idempotency, auth, pagination."""

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from cmms.client import CMMSClient, PermanentError, RetryBudgetExceeded, WorkOrder  # noqa: E402
from cmms.fake import FakeClock, FakeCMMS, Transport  # noqa: E402

W = "2026-11-04T14:05:00Z"


@pytest.fixture
def env():
    clock = FakeClock()
    server = FakeCMMS(clock)
    t = Transport(server)
    c = CMMSClient(t, FakeCMMS.CLIENT_ID, FakeCMMS.CLIENT_SECRET, clock.time, clock.sleep)
    return clock, server, t, c


def posts(t):
    return [x for x in t.calls if x["method"] == "POST" and x["path"] == "/api/v2/work-orders"]


def test_key_is_deterministic_and_distinct():
    k = CMMSClient.idempotency_key
    assert k("pump-04", W) == k("pump-04", W)
    assert k("pump-04", W) != k("pump-03", W) != k("pump-04", "2026-11-04T14:10:00Z")


def test_same_key_on_every_retry_and_header_sent(env):
    clock, server, t, c = env
    t.script([None, "500", "commit-timeout", "503", None])
    wo = c.raise_work_order("pump-04", W, "Outer race", "P2")
    keys = {p["headers"].get("Idempotency-Key") for p in posts(t)}
    assert len(posts(t)) == 4 and len(keys) == 1 and None not in keys
    assert len(server.orders) == 1 and isinstance(wo, WorkOrder)


def test_restart_reuses_key(env):
    clock, server, t, c = env
    c.raise_work_order("pump-04", W, "Outer race", "P2")
    c2 = CMMSClient(t, FakeCMMS.CLIENT_ID, FakeCMMS.CLIENT_SECRET, clock.time, clock.sleep)
    wo = c2.raise_work_order("pump-04", W, "Outer race", "P2")
    assert len(server.orders) == 1 and wo.id == server.orders[0]["id"]


def test_thirty_percent_faults_no_duplicates():
    rng = random.Random(3)
    clock = FakeClock()
    server = FakeCMMS(clock)
    t = Transport(server)
    c = CMMSClient(t, FakeCMMS.CLIENT_ID, FakeCMMS.CLIENT_SECRET, clock.time, clock.sleep, retry_budget_s=600, max_attempts=12)
    faults = []
    for _ in range(2000):
        faults.append(rng.choice(["500", "503", "429", "commit-timeout", "timeout"]) if rng.random() < 0.3 else None)
    t.script(faults)
    for i in range(40):
        c.raise_work_order(f"pump-{i % 4 + 1:02d}", f"2026-11-04T{10 + i // 12:02d}:{(i % 12) * 5:02d}:00Z", "alert", "P3")
    assert len(server.orders) == 40


def test_retry_after_seconds_honoured(env):
    clock, server, t, c = env
    t.script([None, "429", None])
    c.raise_work_order("pump-04", W, "Outer race", "P2")
    assert clock.sleeps == [7.0]


def test_retry_after_http_date_honoured(env):
    clock, server, t, c = env
    t.script([None, "429-date", None])
    c.raise_work_order("pump-04", W, "Outer race", "P2")
    assert len(clock.sleeps) == 1 and clock.sleeps[0] == pytest.approx(11, abs=1)


def test_full_jitter_backoff_bounds(env):
    clock, server, t, c = env
    t.script([None, "500", "500", "500", "500", None])
    c.raise_work_order("pump-04", W, "Outer race", "P2")
    assert len(clock.sleeps) == 4
    for i, s in enumerate(clock.sleeps, start=1):
        assert 0 <= s <= min(20.0, 0.5 * 2 ** i) + 1e-9, (i, s)
    assert len(set(clock.sleeps)) > 1, "no jitter"


def test_no_retry_on_422(env):
    clock, server, t, c = env
    with pytest.raises(PermanentError) as ei:
        c.raise_work_order("", W, "x", "P2")
    assert ei.value.status == 422
    assert len(posts(t)) == 1 and clock.sleeps == []


def test_budget_exhausted_raises_clearly(env):
    clock, server, t, c = env
    t.script([None] + ["503"] * 50)
    with pytest.raises(RetryBudgetExceeded):
        c.raise_work_order("pump-04", W, "Outer race", "P2")
    assert sum(clock.sleeps) <= 60.0
    assert len(posts(t)) <= 6
    assert server.orders == []


def test_retry_after_beyond_budget_fails_fast():
    clock = FakeClock()
    server = FakeCMMS(clock)
    t = Transport(server)
    c = CMMSClient(t, FakeCMMS.CLIENT_ID, FakeCMMS.CLIENT_SECRET, clock.time, clock.sleep, retry_budget_s=5)
    t.script([None, "429"])
    with pytest.raises(RetryBudgetExceeded):
        c.raise_work_order("pump-04", W, "Outer race", "P2")
    assert clock.sleeps == []


def test_timeout_on_every_call(env):
    clock, server, t, c = env
    t.script([None, "timeout", None])
    c.raise_work_order("pump-04", W, "Outer race", "P2")
    c.list_work_orders("pump-04")
    assert all(x["timeout"] and x["timeout"] > 0 for x in t.calls)


def test_token_reused_then_refreshed_on_expiry(env):
    clock, server, t, c = env
    c.raise_work_order("pump-01", W, "a", "P3")
    c.raise_work_order("pump-02", W, "b", "P3")
    assert server.token_requests == 1, "cache the token"
    clock.now += 400  # past the 300 s TTL
    c.raise_work_order("pump-03", W, "c", "P3")
    assert server.token_requests == 2 and len(server.orders) == 3


def test_401_triggers_one_refresh(env):
    clock, server, t, c = env
    c.raise_work_order("pump-01", W, "a", "P3")
    server.tokens.clear()  # server-side revocation: the cached token is now invalid
    c.raise_work_order("pump-02", W, "b", "P3")
    assert server.token_requests == 2 and len(server.orders) == 2


def test_pagination_returns_everything(env):
    clock, server, t, c = env
    for i in range(8):
        c.raise_work_order("pump-04", f"2026-11-04T1{i}:00:00Z", f"alert {i}", "P3")
    c.raise_work_order("pump-01", W, "other", "P3")
    got = c.list_work_orders("pump-04")
    assert len(got) == 8 and len({w.id for w in got}) == 8
    assert all(isinstance(w, WorkOrder) for w in got)
