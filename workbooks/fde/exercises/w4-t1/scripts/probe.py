"""Reproduce the incident against the running gateway (make setup first).

Five customers each look up one product and add it, ten times over, concurrently, the
way a burst of Managed Agents sessions hits the gateway at the top of a promotion. Then
each customer reads their own cart, one at a time, and we compare.
"""

from __future__ import annotations

import asyncio
import re
import secrets
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gateway.app import load_env  # noqa: E402
from gateway.auth import sign_claim  # noqa: E402
from gateway.sessions import digest  # noqa: E402

PRODUCTS = ["AR-1001", "AR-1003", "AR-1004", "AR-1005", "AR-1006"]


async def main() -> int:
    env = load_env(Path(__file__).resolve().parents[1] / "gateway.env")
    base = f"http://{env.get('GATEWAY_HOST', '127.0.0.1')}:{env.get('GATEWAY_PORT', '18410')}"
    run = secrets.token_hex(3)
    customers = [f"cust-{name}-{run}" for name in ("ana", "bo", "chen", "dara", "eli")]
    tokens = {c: sign_claim(c, env["GATEWAY_SECRET"]) for c in customers}
    mismatched = held = 0

    async with httpx.AsyncClient(base_url=base, timeout=10) as client:

        async def call(customer: str, tool: str, args: dict) -> dict:
            nonlocal mismatched, held
            r = await client.post(
                f"/tools/{tool}", json=args, headers={"Authorization": f"Bearer {tokens[customer]}"}
            )
            body = r.json()
            if body.get("acting_for") != digest(customer):
                mismatched += 1
            if body.get("blocked"):
                held += 1
            return body

        async def flow(customer: str, product: str) -> None:
            await call(customer, "get_product_details", {"product_id": product})
            await call(customer, "add_to_cart", {"product_id": product, "quantity": 1})

        await asyncio.gather(
            *[flow(c, p) for _ in range(10) for c, p in zip(customers, PRODUCTS, strict=True)]
        )

        leaks = 0
        print(f"run {run}: 100 concurrent tool calls from 5 customers")
        for customer, own in zip(customers, PRODUCTS, strict=True):
            body = await call(customer, "get_cart", {})
            ids = sorted(set(re.findall(r"AR-\d{4}", body["result_text"])))
            foreign = [i for i in ids if i != own]
            leaks += bool(foreign)
            flag = "LEAK" if foreign else ("ok  " if own in ids else "MISS")
            print(f"  {flag} {customer:<18} expected only {own}; cart holds {ids}")
    print(f"responses acting for the wrong customer: {mismatched}")
    print(f"calls held by a gate (blocked):          {held}")
    print(f"customers whose cart holds another customer's item: {leaks}/5")
    print("(each customer's session id is gw-<digest of their id>; see run/gateway.log audit lines)")
    return 1 if leaks or mismatched else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
