"""Test helper: walk every page of GET /v1/contacts."""


async def walk(client, tenant, limit, on_page=None):
    seen, cursor, pages = [], None, 0
    while True:
        params = {"limit": limit} | ({"cursor": cursor} if cursor else {})
        r = await client.get("/v1/contacts", params=params, headers={"X-Tenant-Id": tenant})
        assert r.status_code == 200, r.text
        body = r.json()
        pages += 1
        seen += [x["id"] for x in body["data"]]
        if on_page:
            await on_page(pages)
        cursor = body["next_cursor"]
        if not cursor or pages > 10000:
            return seen
