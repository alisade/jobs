"""Hidden checks for w1-t1: one bounded retry layer with jitter, correct error mapping, replay
thresholds on the 2026-11-09 traffic, and guards."""

from __future__ import annotations

import json

import pytest
from w1t1_hidden_support import ROOT, StubBedrock

from replay.sim import load_release, run, sdk_total_attempts


@pytest.fixture(scope="module")
def release():
    return load_release(ROOT, "hidden_answer_svc")


@pytest.fixture(scope="module")
def replay_current(release):
    return run(release, "2026-11-09")["summary"]


def _app(release):
    return release.resilience.APP_POLICY


def test_total_attempts_per_request_at_most_4(release):
    s = run(release, "2026-11-09", always_throttle=True)["summary"]
    assert s["max_attempts_per_request"] <= 4, (
        f"one request can make {s['max_attempts_per_request']} Bedrock calls "
        f"(sdk total {s['sdk_total_attempts']} x app {s['app_max_attempts']})")


def test_single_retry_layer(release):
    sdk_total, _ = sdk_total_attempts(release)
    assert sdk_total == 1 or _app(release).max_attempts == 1, "retries must live in one layer, not both"


def test_retrying_layer_uses_capped_full_jitter(release):
    app = _app(release)
    sdk_total, mode = sdk_total_attempts(release)
    if app.max_attempts > 1:
        assert app.delay(2, lambda: 0.0) == 0.0, "full jitter: the lower bound is 0"
        hi = app.delay(2, lambda: 0.999)
        assert hi > 0.0
        assert app.delay(2, lambda: 0.5) != hi, "delay must depend on the random draw"
        assert app.delay(12, lambda: 0.999) <= 10.0, "a single delay must be capped"
    else:
        assert sdk_total > 1, "no retry at all: the 09:02 login wave would fail every throttled request"
        assert mode in ("standard", "adaptive"), "use a botocore mode with jittered backoff"


@pytest.mark.parametrize("code,status", [("ValidationException", 400), ("AccessDeniedException", 500)])
def test_non_retryable_errors_fail_fast(code, status):
    from answer_svc import service
    b = StubBedrock()
    b.error(code, 400 if code == "ValidationException" else 403)
    slept = []
    with b.stub:
        r = service.answer("Where is SH-10001?", b.client, sleep=slept.append)
    assert b.calls == 1, f"{code} must not be retried"
    assert r["statusCode"] == status
    assert slept == []


def test_throttling_degrades_with_retry_after():
    from answer_svc import service
    b = StubBedrock()
    for _ in range(4):
        b.error("ThrottlingException", 429)
    with b.stub:
        r = service.answer("Where is SH-10001?", b.client, sleep=lambda s: None)
    assert b.calls <= 4
    assert r["statusCode"] == 503, "a throttled answer is degraded (503), not an internal error"
    headers = {k.lower(): v for k, v in r.get("headers", {}).items()}
    assert "retry-after" in headers and int(headers["retry-after"]) > 0
    assert "internal" not in r["body"]


def test_throttle_then_success_within_budget():
    from answer_svc import service
    b = StubBedrock()
    b.error("ThrottlingException", 429)
    b.ok("Delivered.")
    with b.stub:
        r = service.answer("Where is SH-10002?", b.client, sleep=lambda s: None)
    # With retries in the SDK layer (disabled in this stub client) a single throttle surfaces as 503;
    # with retries in the app layer the second response answers. Both are acceptable, a 500 is not.
    assert r["statusCode"] in (200, 503)


def test_replay_error_rate(replay_current):
    assert replay_current["error_rate"] < 0.05, replay_current


def test_replay_latency_and_amplification(replay_current):
    assert replay_current["p95_ms"] < 8000, replay_current
    assert replay_current["amplification"] < 1.5, replay_current


def test_replay_does_not_depend_on_reserved_concurrency(release):
    s = run(release, "2026-11-09", concurrency=100)["summary"]
    assert s["error_rate"] < 0.05 and s["p95_ms"] < 8000, s


def test_guard_previous_release_replay_unchanged():
    prev = load_release(ROOT / "evidence" / "previous_release", "hidden_prev_answer_svc")
    s = run(prev, "2026-11-02")["summary"]
    assert s["error_rate"] < 0.03 and s["amplification"] < 1.1, "the environment (replay/, evidence/) must stay as shipped"


def test_guard_success_body():
    from answer_svc import service
    b = StubBedrock()
    b.ok("SH-10001 arrives 2026-11-16.")
    with b.stub:
        r = service.answer("When does SH-10001 arrive?", b.client, sleep=lambda s: None)
    assert r["statusCode"] == 200 and json.loads(r["body"]) == {"answer": "SH-10001 arrives 2026-11-16."}
