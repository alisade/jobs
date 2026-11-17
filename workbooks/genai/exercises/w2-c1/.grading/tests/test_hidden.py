"""Hidden checks for genai/w2-c1 (service half)."""

import json
import pathlib

from catalog.app import create_app
from catalog.db import make_engine
from conftest import client  # noqa: F401  (shared fixture)

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROBLEM = "application/problem+json"


def _all(client, **params):
    out, cursor, pages = [], None, 0
    while True:
        p = dict(params)
        if cursor:
            p["cursor"] = cursor
        r = client.get("/products", params=p)
        assert r.status_code == 200, r.text
        body = r.json()
        out.extend(body["items"])
        cursor = body["next_cursor"]
        pages += 1
        assert pages < 50
        if not cursor:
            return out, pages


def test_page_shape_and_default_order(client):
    body = client.get("/products").json()
    assert set(body) == {"items", "next_cursor"}
    items = body["items"]
    assert len(items) == 20
    keys = [(i["price_cents"], i["sku"]) for i in items]
    assert keys == sorted(keys)
    assert body["next_cursor"]


def test_search_is_case_insensitive_over_name_and_description(client):
    skus = {i["sku"] for i in _all(client, q="TENT")[0]}
    assert {"KO-TENT-1P", "KO-TENT-2P", "KO-TENT-3P", "KO-TENT-6P"} <= skus
    desc = {i["sku"] for i in _all(client, q="rotomolded")[0]}
    assert desc == {"KO-COOL-45", "KO-COOL-20"}


def test_filters_combine(client):
    items = _all(client, category="furniture", max_price_cents=6900)[0]
    assert items and all(i["category"] == "furniture" and i["price_cents"] <= 6900 for i in items)
    assert {i["sku"] for i in items} == {"KO-CHAIR-1", "KO-TABLE-1", "KO-HAMK-1", "KO-RUG-1"}


def test_in_stock_at_uses_available_at_that_store(client):
    items = _all(client, in_stock_at="012")[0]
    for i in items:
        d = client.get(f"/products/{i['sku']}").json()
        assert next(s for s in d["stock"] if s["store_id"] == "012")["available"] > 0
    assert len(items) < 40


def test_cursor_walk_returns_every_item_once_in_order(client):
    items, pages = _all(client, limit=7)
    assert pages == 6
    skus = [i["sku"] for i in items]
    assert len(skus) == 40 and len(set(skus)) == 40
    keys = [(i["price_cents"], i["sku"]) for i in items]
    assert keys == sorted(keys)  # ties on price broken by sku, no gaps across pages


def test_page_size_is_capped(client):
    assert client.get("/products", params={"limit": 51}).status_code == 422
    assert len(client.get("/products", params={"limit": 50}).json()["items"]) == 40


def test_bad_cursor_is_a_400_problem(client):
    r = client.get("/products", params={"cursor": "not-a-cursor"})
    assert r.status_code == 400
    assert r.headers["content-type"].startswith(PROBLEM)


def test_unknown_sku_is_a_404_problem(client):
    r = client.get("/products/KO-NOPE")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith(PROBLEM)
    body = r.json()
    assert set(body) >= {"type", "title", "status", "detail"}
    assert body["status"] == 404 and body["type"].startswith("https://")


def _avail(client, sku, store):
    d = client.get(f"/products/{sku}").json()
    return next(s for s in d["stock"] if s["store_id"] == store)["available"]


def test_reservation_and_idempotent_replay(client):
    before = _avail(client, "KO-TENT-2P", "012")
    assert before >= 2
    body = {"sku": "KO-TENT-2P", "store_id": "012", "quantity": 2}
    h = {"Idempotency-Key": "chk-7781-aaaa"}
    r1 = client.post("/inventory/reservations", json=body, headers=h)
    assert r1.status_code == 201, r1.text
    r2 = client.post("/inventory/reservations", json=body, headers=h)
    assert r2.status_code == 201
    assert r1.json() == r2.json()
    assert r1.json()["available_after"] == before - 2
    assert _avail(client, "KO-TENT-2P", "012") == before - 2


def test_same_key_different_body_is_rejected(client):
    h = {"Idempotency-Key": "chk-7782-bbbb"}
    assert client.post("/inventory/reservations", json={"sku": "KO-TENT-2P", "store_id": "012", "quantity": 1}, headers=h).status_code == 201
    r = client.post("/inventory/reservations", json={"sku": "KO-TENT-2P", "store_id": "012", "quantity": 2}, headers=h)
    assert r.status_code == 422
    assert r.headers["content-type"].startswith(PROBLEM)


def test_insufficient_stock_is_409_and_changes_nothing(client):
    before = _avail(client, "KO-PACK-45", "087")
    r = client.post("/inventory/reservations", json={"sku": "KO-PACK-45", "store_id": "087", "quantity": before + 1},
                    headers={"Idempotency-Key": "chk-7783-cccc"})
    assert r.status_code == 409
    assert r.headers["content-type"].startswith(PROBLEM)
    assert _avail(client, "KO-PACK-45", "087") == before


def test_two_keys_cannot_oversell(client):
    before = _avail(client, "KO-LAMP-1", "045")
    assert before >= 1
    ok = client.post("/inventory/reservations", json={"sku": "KO-LAMP-1", "store_id": "045", "quantity": before},
                     headers={"Idempotency-Key": "chk-7784-dddd"})
    assert ok.status_code == 201
    again = client.post("/inventory/reservations", json={"sku": "KO-LAMP-1", "store_id": "045", "quantity": 1},
                        headers={"Idempotency-Key": "chk-7785-eeee"})
    assert again.status_code == 409


def test_missing_idempotency_key_is_rejected(client):
    r = client.post("/inventory/reservations", json={"sku": "KO-LAMP-1", "store_id": "045", "quantity": 1})
    assert 400 <= r.status_code < 500


def test_operation_ids():
    spec = create_app(make_engine()).openapi()
    ids = {op["operationId"] for p in spec["paths"].values() for op in p.values()}
    assert ids == {"health", "listProducts", "getProduct", "createReservation"}


def test_committed_contract_matches_the_service():
    committed = json.loads((ROOT / "contracts" / "openapi.json").read_text())
    assert committed == create_app(make_engine()).openapi(), "contracts/openapi.json is stale: run make contract"
