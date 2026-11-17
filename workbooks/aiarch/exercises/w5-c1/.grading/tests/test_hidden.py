import threading

import pytest

from fixtures_lh import NOW
from lighthouse_state import store


def test_table_has_ttl_and_at_most_two_gsis(table):
    c = table.meta.client
    ttl = c.describe_time_to_live(TableName=table.name)["TimeToLiveDescription"]
    assert ttl["TimeToLiveStatus"] == "ENABLED" and ttl["AttributeName"] == "ttl"
    assert len(table.global_secondary_indexes or []) <= 2
    assert table.billing_mode_summary["BillingMode"] == "PAY_PER_REQUEST"


def test_recent_sessions_window_and_order(table):
    for i, age_days in enumerate([0.1, 2, 6.9, 7.5, 20]):
        store.start_session(table, "lwong", "access_reviews", f"s{i}", NOW - age_days * 86400)
    store.start_session(table, "mchen", "it_requests", "other", NOW)
    got = [s["session_id"] for s in store.recent_sessions(table, "lwong", NOW)]
    assert got == ["s0", "s1", "s2"]


def test_get_session_by_id(table):
    store.start_session(table, "lwong", "access_reviews", "sess-77", NOW)
    s = store.get_session(table, "sess-77")
    assert s and s["user"] == "lwong"
    assert store.get_session(table, "nope") is None


def test_duplicate_session_id_same_instant_rejected(table):
    from botocore.exceptions import ClientError
    store.start_session(table, "lwong", "a", "dup", NOW)
    with pytest.raises(ClientError):
        store.start_session(table, "lwong", "a", "dup", NOW)


def test_run_once_failure_allows_retry(table):
    def boom():
        raise RuntimeError("API 503")
    with pytest.raises(RuntimeError):
        store.run_once(table, "k1", boom, NOW)
    assert store.run_once(table, "k1", lambda: {"ok": True}, NOW) == {"ok": True}


def test_run_once_in_progress(table):
    gate = threading.Event()
    out = {}

    def slow():
        gate.wait(5)
        return {"ok": 1}

    t = threading.Thread(target=lambda: out.setdefault("r", store.run_once(table, "k2", slow, NOW)))
    t.start()
    import time
    for _ in range(100):
        if table.get_item(Key={"PK": "IDEMP#k2", "SK": "IDEMP"}).get("Item"):
            break
        time.sleep(0.02)
    with pytest.raises(store.InProgress):
        store.run_once(table, "k2", lambda: {"ok": 2}, NOW)
    gate.set()
    t.join(5)
    assert out["r"] == {"ok": 1}


def test_idempotency_item_expires(table):
    store.run_once(table, "k3", lambda: {"ok": 1}, NOW)
    item = table.get_item(Key={"PK": "IDEMP#k3", "SK": "IDEMP"})["Item"]
    assert item["ttl"] == int(item["ttl"]) and NOW < int(item["ttl"]) < NOW + 7 * 86400


def test_cost_with_cache_tokens_and_per_day(table, spans, prices):
    for s in spans:
        store.record_usage(table, s, prices)
    assert store.daily_cost(table, "access_reviews", "2026-11-12", "2026-11-13") == [("2026-11-12", 0.0216), ("2026-11-13", 0.0165)]


def test_cost_for_day_all_agents(table, spans, prices):
    for s in spans:
        store.record_usage(table, s, prices)
    assert store.cost_for_day(table, "2026-11-12") == {"orchestrator": 0.00335, "access_reviews": 0.0216}


def test_calls_and_tokens_accumulate_exactly(table, spans, prices):
    for s in spans:
        store.record_usage(table, s, prices)
    item = table.get_item(Key={"PK": "COST#orchestrator", "SK": "DAY#2026-11-12"})["Item"]
    assert int(item["calls"]) == 2 and int(item["input_tokens"]) == 2500 and int(item["cost_micro_usd"]) == 3350


def test_unknown_model_price_raises(table, prices):
    span = {"start_time": "2026-11-13T00:00:00Z", "attributes": {"gen_ai.agent.name": "x", "gen_ai.request.model": "meta.llama",
            "gen_ai.usage.input_tokens": 1, "gen_ai.usage.output_tokens": 1}}
    with pytest.raises(KeyError):
        store.record_usage(table, span, prices)


def test_optimistic_locking(table):
    store.create_approval(table, "AR-9")
    v = store.decide(table, "AR-9", "APPROVED", "lwong", 1)
    assert v == 2
    with pytest.raises(store.Conflict):
        store.decide(table, "AR-9", "REJECTED", "tkhan", 1)


def test_cannot_decide_twice_even_with_current_version(table):
    store.create_approval(table, "AR-10")
    v = store.decide(table, "AR-10", "APPROVED", "lwong", 1)
    with pytest.raises(store.Conflict):
        store.decide(table, "AR-10", "REJECTED", "lwong", v)
