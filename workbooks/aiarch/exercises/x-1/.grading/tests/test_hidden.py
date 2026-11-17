from collections import Counter
from pathlib import Path

from fixtures_lh import NOW
from lighthouse_sessions import sessions


def _hk(table):
    gsi = [g for g in table.global_secondary_indexes if g["IndexName"] == sessions.INDEX][0]
    return gsi["KeySchema"][0]["AttributeName"]


def test_spread_is_even(table):
    hk = _hk(table)
    c = Counter(sessions.open_session(table, f"sess-{i:05d}", "u", "2026-11-13T09:00:00Z", NOW)[hk] for i in range(1000))
    assert len(c) >= 8 and max(c.values()) < 1000 * 0.25, c


def test_shard_is_stable_for_a_session(table):
    hk = _hk(table)
    a = sessions.open_session(table, "same", "u", "2026-11-13T09:00:00Z", NOW)[hk]
    b = sessions.open_session(table, "same", "u", "2026-11-13T09:00:00Z", NOW)[hk]
    assert a == b


def test_closed_sessions_leave_the_index(table):
    for i in range(20):
        sessions.open_session(table, f"s-{i}", "u", "2026-11-13T09:00:00Z", NOW)
    for i in range(0, 20, 2):
        sessions.close_session(table, f"s-{i}")
    assert sorted(sessions.list_active(table)) == sorted(f"s-{i}" for i in range(1, 20, 2))
    hk = _hk(table)
    closed = table.get_item(Key={"session_id": "s-0"})["Item"]
    assert hk not in closed, "sparse index: a closed session must not keep the index key"
    assert closed["status"] == "CLOSED"


def test_list_active_paginates_across_shards(table):
    for i in range(120):
        sessions.open_session(table, f"p-{i}", "u", f"2026-11-13T09:{i % 60:02d}:00Z", NOW)
    got = sessions.list_active(table)
    assert len(got) == 120 and len(set(got)) == 120


def test_ttl_epoch_seconds(table):
    item = sessions.open_session(table, "t", "u", "2026-11-13T09:00:00Z", NOW)
    assert isinstance(item["ttl"], int) and item["ttl"] == int(NOW) + sessions.SESSION_TTL_SECONDS


def test_table_still_on_demand_with_ttl(table):
    assert table.billing_mode_summary["BillingMode"] == "PAY_PER_REQUEST"
    ttl = table.meta.client.describe_time_to_live(TableName=table.name)["TimeToLiveDescription"]
    assert ttl["AttributeName"] == "ttl"


def test_answer_names_gsi_hot_partition():
    t = Path("ANSWER.md").read_text().lower()
    assert ("gsi" in t or "index" in t) and ("hot" in t or "partition" in t) and "by-status" in t
