from fixtures_lh import NOW
from lighthouse_sessions import sessions


def _index_keys(table):
    gsi = [g for g in table.global_secondary_indexes if g["IndexName"] == sessions.INDEX][0]
    return gsi["KeySchema"][0]["AttributeName"]


def test_index_partition_key_is_not_a_single_value(table):
    hk = _index_keys(table)
    vals = set()
    for i in range(200):
        item = sessions.open_session(table, f"s-{i:04d}", f"u{i}", "2026-11-13T09:00:00Z", NOW)
        vals.add(item[hk])
    assert len(vals) >= 8, f"all {len(vals)} index partition key values: {sorted(vals)[:5]}"


def test_list_active_returns_open_sessions(table):
    for i in range(30):
        sessions.open_session(table, f"s-{i}", "u", "2026-11-13T09:00:00Z", NOW)
    assert sorted(sessions.list_active(table)) == sorted(f"s-{i}" for i in range(30))
