"""Hidden tests for fde/w4-t1: identity is request-scoped under any interleaving."""

from __future__ import annotations

import asyncio

import pytest
from w4t1_hidden_support import (
    CUSTOMERS,
    PRODUCTS,
    SECRET,
    call,
    cart_of,
    client_for,
    digest,
    make_app,
    run_concurrent,
)

from gateway import identity
from gateway.auth import sign_claim


async def test_fifty_interleaved_requests_from_five_customers_never_cross():
    app = make_app(latency_s=0.003)
    responses = await run_concurrent(app, rounds=5)  # 5 customers x 5 flows x 2 calls = 50
    assert len(responses) == 50
    assert all(r["acting_for"] == digest(c) for c, r in responses)
    for customer, product in zip(CUSTOMERS, PRODUCTS, strict=True):
        assert await cart_of(app, customer) == {product: 5}, customer


async def test_no_provenance_holds_under_concurrency():
    """A lookup made as one customer must count as provenance for that same customer."""
    app = make_app(latency_s=0.004)
    responses = await run_concurrent(app, rounds=2)
    held = [(c, r) for c, r in responses if r["blocked"]]
    assert not held, held[:2]


@pytest.mark.parametrize("latency", [0.0, 0.001, 0.02])
async def test_isolation_holds_at_any_redis_latency(latency):
    app = make_app(latency_s=latency)
    responses = await run_concurrent(app)
    assert all(r["acting_for"] == digest(c) for c, r in responses)


async def test_identity_does_not_outlive_the_request():
    app = make_app()
    async with client_for(app) as client:
        await call(client, "cust-late", "get_cart", {})
    with pytest.raises(identity.Unauthenticated):
        identity.current_principal()


async def test_bind_in_one_task_is_invisible_to_another():
    seen: dict[str, str] = {}
    gate = asyncio.Event()

    async def worker(name: str) -> None:
        handle = identity.bind(name)
        try:
            if name == "first":
                await gate.wait()  # "second" binds while "first" is suspended
            else:
                gate.set()
            await asyncio.sleep(0)
            seen[name] = identity.current_principal()
        finally:
            identity.release(handle)

    await asyncio.gather(worker("first"), worker("second"))
    assert seen == {"first": "first", "second": "second"}


async def test_release_restores_the_outer_binding():
    outer = identity.bind("outer")
    try:
        inner = identity.bind("inner")
        identity.release(inner)
        assert identity.current_principal() == "outer"
    finally:
        identity.release(outer)


async def test_auth_still_enforced():
    app = make_app()
    async with client_for(app) as client:
        assert (await client.post("/tools/get_cart", json={})).status_code == 401
        bad = sign_claim("cust-x", "wrong-secret")
        r = await client.post("/tools/get_cart", json={}, headers={"Authorization": f"Bearer {bad}"})
        assert r.status_code == 401
        ok = sign_claim("cust-x", SECRET)
        r = await client.post("/tools/get_cart", json={}, headers={"Authorization": f"Bearer {ok}"})
        assert r.status_code == 200 and r.json()["acting_for"] == digest("cust-x")


async def test_slow_request_keeps_its_identity_while_others_finish():
    app = make_app(latency_s=0.0)
    async with client_for(app) as client:
        slow = asyncio.create_task(call(client, "cust-slow", "get_cart", {}))
        fast = [call(client, f"cust-fast-{i}", "get_cart", {}) for i in range(10)]
        results = await asyncio.gather(*fast)
        assert all(r["acting_for"] == digest(f"cust-fast-{i}") for i, r in enumerate(results))
        assert (await slow)["acting_for"] == digest("cust-slow")
