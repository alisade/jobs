"""Visible tests: one customer works; concurrent customers stay isolated."""

from __future__ import annotations

from w4t1_support import CUSTOMERS, PRODUCTS, call, cart_of, client_for, digest, run_concurrent


async def test_one_customer_alone_gets_their_own_cart(app):
    async with client_for(app) as client:
        await call(client, "cust-solo", "get_product_details", {"product_id": "AR-1001"})
        added = await call(client, "cust-solo", "add_to_cart", {"product_id": "AR-1001", "quantity": 2})
    assert added["acting_for"] == digest("cust-solo")
    assert not added["is_error"] and added["blocked"] is None, added
    assert await cart_of(app, "cust-solo") == {"AR-1001": 2}


async def test_requests_are_served_as_the_customer_who_sent_them(app):
    responses = await run_concurrent(app)
    wrong = [(c, r["acting_for"]) for c, r in responses if r["acting_for"] != digest(c)]
    assert not wrong, f"{len(wrong)} of {len(responses)} responses acted for another customer"


async def test_five_concurrent_customers_each_see_only_their_own_cart(app):
    await run_concurrent(app)
    for customer, product in zip(CUSTOMERS, PRODUCTS, strict=True):
        assert await cart_of(app, customer) == {product: 1}, customer
