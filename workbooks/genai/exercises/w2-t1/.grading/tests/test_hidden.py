"""Hidden checks for genai/w2-t1: the event loop stays responsive and promotions degrade."""

import asyncio
import time

import pytest

from conftest import asgi_client, run, timed_get
from catalog_search.app import app, get_promotions
from catalog_search.promotions_sdk import PromotionsClient


def _use(client):
    app.dependency_overrides[get_promotions] = lambda: client


@pytest.fixture(autouse=True)
def _clear():
    yield
    app.dependency_overrides.clear()


def test_healthz_answers_while_searches_are_in_flight():
    _use(PromotionsClient(latency_s=0.25))

    async def go():
        async with asgi_client() as c:
            searches = [asyncio.create_task(c.get("/search", params={"q": "tent"})) for _ in range(8)]
            due = time.perf_counter() + 0.02  # the probe is due 20 ms after the searches start
            await asyncio.sleep(0.02)
            r = await c.get("/healthz")
            dt = time.perf_counter() - due
            await asyncio.gather(*searches)
            return r, dt

    r, dt = run(go())
    assert r.status_code == 200
    assert dt < 0.2, f"/healthz took {dt:.2f}s while searches were running (event loop blocked?)"


def test_concurrent_searches_overlap():
    _use(PromotionsClient(latency_s=0.25))

    async def go():
        async with asgi_client() as c:
            t0 = time.perf_counter()
            rs = await asyncio.gather(*[c.get("/search", params={"q": "pack"}) for _ in range(8)])
            return rs, time.perf_counter() - t0

    rs, dt = run(go())
    assert all(r.status_code == 200 for r in rs)
    assert dt < 1.0, f"8 searches took {dt:.2f}s; with 0.25s promotions each they should overlap"


def test_slow_promotions_degrade_within_budget():
    _use(PromotionsClient(latency_s=1.5))

    async def go():
        async with asgi_client() as c:
            return await timed_get(c, "/search?q=tent")

    r, dt = run(go())
    assert r.status_code == 200
    body = r.json()
    assert dt < 0.8, f"search waited {dt:.2f}s on a 1.5s promotions call; bound it"
    assert body["promotions_degraded"] is True
    assert body["count"] >= 3
    assert all("badge" not in x for x in body["results"])


def test_promotions_error_degrades_not_500():
    _use(PromotionsClient(latency_s=0.01, fail=True))

    async def go():
        async with asgi_client() as c:
            return await c.get("/search", params={"q": "lantern"})

    r = run(go())
    assert r.status_code == 200
    assert r.json()["promotions_degraded"] is True
    assert r.json()["results"][0]["sku"] == "KO-LAMP-1"


def test_healthy_promotions_not_flagged_degraded():
    _use(PromotionsClient(latency_s=0.01))

    async def go():
        async with asgi_client() as c:
            return await c.get("/search", params={"q": "ridgeline"})

    body = run(go()).json()
    assert body["promotions_degraded"] is False
    assert body["results"][0]["badge"].startswith("Holiday deal")


def test_no_results_does_not_call_promotions():
    client = PromotionsClient(latency_s=0.01)
    _use(client)

    async def go():
        async with asgi_client() as c:
            return await c.get("/search", params={"q": "kayak"})

    body = run(go()).json()
    assert body["count"] == 0
    assert client.calls == 0


def test_filters_and_limits_unchanged():
    _use(PromotionsClient(latency_s=0.01))

    async def go():
        async with asgi_client() as c:
            a = await c.get("/search", params={"q": "jacket", "category": "apparel"})
            b = await c.get("/search", params={"q": "e", "limit": 2})
            d = await c.get("/search", params={"q": "e", "limit": 99})
            return a, b, d

    a, b, d = run(go())
    assert {x["sku"] for x in a.json()["results"]} == {"KO-JKT-RAIN", "KO-JKT-FLC"}
    assert b.json()["count"] == 2
    assert d.status_code == 422
