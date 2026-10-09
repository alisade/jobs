"""Helpers for the visible tests: the gateway in-process behind httpx's ASGI transport,
and customer flows that interleave on the simulated Redis round trips."""

from __future__ import annotations

import asyncio

import httpx

from gateway.app import create_app
from gateway.auth import sign_claim
from gateway.sessions import digest, session_id_for
from shopping_agent import ShoppingSessionContext

SECRET = "test-secret"
# Plain, in-stock retail products: one per customer, so any cross-customer write shows.
PRODUCTS = ["AR-1001", "AR-1003", "AR-1004", "AR-1005", "AR-1006"]
CUSTOMERS = [f"cust-{n}" for n in ("ana", "bo", "chen", "dara", "eli")]


def make_app(latency_s: float = 0.005):
    return create_app(secret=SECRET, redis_latency_s=latency_s)


def client_for(app) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://gw")


async def call(client, customer: str, tool: str, args: dict) -> dict:
    token = sign_claim(customer, SECRET)
    r = await client.post(f"/tools/{tool}", json=args, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    return r.json()


async def flow(client, customer: str, product_id: str, responses: list) -> None:
    """Look the product up (provenance), then add one."""
    responses.append((customer, await call(client, customer, "get_product_details", {"product_id": product_id})))
    responses.append((customer, await call(client, customer, "add_to_cart", {"product_id": product_id, "quantity": 1})))


async def cart_of(app, customer: str) -> dict[str, int]:
    cart = await app.backend.get_cart(
        ShoppingSessionContext(session_id=session_id_for(customer), user_id=customer)
    )
    return {i.product_id: i.quantity for i in cart.items}


async def run_concurrent(app, rounds: int = 1) -> list:
    responses: list = []
    async with client_for(app) as client:
        await asyncio.gather(
            *[
                flow(client, customer, product, responses)
                for _ in range(rounds)
                for customer, product in zip(CUSTOMERS, PRODUCTS, strict=True)
            ]
        )
    return responses


__all__ = ["CUSTOMERS", "PRODUCTS", "SECRET", "call", "cart_of", "client_for", "digest", "make_app", "run_concurrent"]
