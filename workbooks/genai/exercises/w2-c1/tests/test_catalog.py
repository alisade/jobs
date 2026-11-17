def test_list_products_returns_a_page(client):
    r = client.get("/products", params={"q": "tent"})
    assert r.status_code == 200


def test_get_product(client):
    r = client.get("/products/KO-TENT-2P")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Ridgeline 2P Tent"
    assert {s["store_id"] for s in body["stock"]} == {"012", "045", "087"}


def test_healthz(client):
    assert client.get("/healthz").json() == {"status": "ok"}
