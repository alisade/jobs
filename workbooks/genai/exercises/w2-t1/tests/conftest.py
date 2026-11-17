import asyncio
import time

import httpx
import pytest

from catalog_search.app import app, get_promotions
from catalog_search.promotions_sdk import PromotionsClient


@pytest.fixture
def promo():
    client = PromotionsClient(latency_s=0.25)
    app.dependency_overrides[get_promotions] = lambda: client
    yield client
    app.dependency_overrides.clear()


def run(coro, timeout=10.0):
    return asyncio.run(asyncio.wait_for(coro, timeout))


async def timed_get(client: httpx.AsyncClient, url: str):
    t0 = time.perf_counter()
    r = await client.get(url)
    return r, time.perf_counter() - t0


def asgi_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")
