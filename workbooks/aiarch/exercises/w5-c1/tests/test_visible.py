from fixtures_lh import NOW
from lighthouse_state import store


def test_session_ttl_is_epoch_seconds_30_days_out(table):
    item = store.start_session(table, "lwong", "access_reviews", "s-1", NOW)
    assert isinstance(item["ttl"], int) and item["ttl"] == int(NOW) + 30 * 86400


def test_retry_does_not_repeat_the_side_effect(table):
    calls = []
    fn = lambda: calls.append(1) or {"request_id": "AR-1301"}  # noqa: E731
    a = store.run_once(table, "tooluse-abc", fn, NOW)
    b = store.run_once(table, "tooluse-abc", fn, NOW)
    assert a == b == {"request_id": "AR-1301"} and len(calls) == 1


def test_daily_cost(table, spans, prices):
    for s in spans:
        store.record_usage(table, s, prices)
    assert store.daily_cost(table, "orchestrator", "2026-11-12", "2026-11-12") == [("2026-11-12", 0.00335)]
