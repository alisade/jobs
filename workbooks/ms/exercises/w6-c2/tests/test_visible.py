"""Visible tests: happy paths. Hidden tests cover limits, failures and edge cases."""
from woodgrove_sync.client import DataverseClient, TokenStore

SET = "contoso_assets"
COLS = ["contoso_assetcode", "contoso_name", "contoso_site"]


def test_list_all_follows_paging(server):
    server.fake.seed(7)
    client = DataverseClient(server.api_url)
    rows = client.list_all(SET, COLS, page_size=3)
    assert len(rows) == 7
    assert {r["contoso_assetcode"] for r in rows} == {f"A-{i:04d}" for i in range(1, 8)}


def test_upsert_creates_then_updates(server):
    client = DataverseClient(server.api_url)
    assert client.upsert_by_key(SET, {"contoso_assetcode": "W-100"}, {"contoso_name": "Chiller"}) == "created"
    assert client.upsert_by_key(SET, {"contoso_assetcode": "W-100"}, {"contoso_name": "Chiller 2"}) == "updated"
    assert server.fake.by_code("W-100")["contoso_name"] == "Chiller 2"
    assert server.fake.count() == 1


def test_batch_create_returns_ids_in_order(server):
    client = DataverseClient(server.api_url)
    rows = [{"contoso_assetcode": f"B-{i}", "contoso_name": f"Valve {i}"} for i in range(3)]
    ids = client.batch_create(SET, rows)
    assert len(ids) == 3
    for i, rid in enumerate(ids):
        assert server.fake.rows[rid]["contoso_assetcode"] == f"B-{i}"


def test_initial_sync_loads_everything_and_saves_delta_link(server):
    server.fake.seed(4)
    client = DataverseClient(server.api_url)
    store, seen = TokenStore(), []
    stats = client.sync_changes(SET, COLS, store, seen.append, lambda _id: None)
    assert stats == {"upserts": 4, "deletes": 0}
    assert len(seen) == 4
    assert store.delta_link and "$deltatoken=" in store.delta_link
