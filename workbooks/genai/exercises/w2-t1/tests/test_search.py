from conftest import asgi_client, run


def test_search_finds_tents(promo):
    async def go():
        async with asgi_client() as c:
            return await c.get("/search", params={"q": "tent"})

    r = run(go())
    assert r.status_code == 200
    skus = [x["sku"] for x in r.json()["results"]]
    assert "KO-TENT-2P" in skus and "KO-TENT-3P" in skus


def test_search_adds_promotion_badges(promo):
    async def go():
        async with asgi_client() as c:
            return await c.get("/search", params={"q": "ridgeline"})

    body = run(go()).json()
    assert body["results"][0]["badge"] == "Holiday deal: 15% off"


def test_healthz():
    async def go():
        async with asgi_client() as c:
            return await c.get("/healthz")

    assert run(go()).json() == {"status": "ok"}
