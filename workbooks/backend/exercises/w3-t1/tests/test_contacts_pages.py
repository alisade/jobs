from contacts_api.seed import make_rows
from testkit import walk

T = "app-partner-portal"


async def test_first_page_shape(make_client):
    client, _ = await make_client(make_rows(T, 30, 0))
    async with client:
        r = await client.get("/v1/contacts", params={"limit": 10}, headers={"X-Tenant-Id": T})
        assert r.status_code == 200
        body = r.json()
        assert len(body["data"]) == 10 and body["next_cursor"]
        assert [x["created_at"] for x in body["data"]] == sorted(x["created_at"] for x in body["data"])


async def test_walk_without_ties_returns_everything(make_client):
    rows = make_rows(T, 250, 0)
    client, _ = await make_client(rows)
    async with client:
        seen = await walk(client, T, 40)
    assert sorted(seen) == sorted(r["id"] for r in rows)


async def test_walk_like_the_partner(make_client):
    rows = make_rows(T, 1931, 500)
    client, _ = await make_client(rows)
    async with client:
        seen = await walk(client, T, 100)
    missing = {r["id"] for r in rows} - set(seen)
    assert not missing, f"{len(missing)} contacts never returned"
    assert len(seen) == len(set(seen)), "a contact was returned twice"
