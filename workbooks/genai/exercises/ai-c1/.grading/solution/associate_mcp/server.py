"""MCP server for Kestrel store associates. Reference solution."""


import secrets
import time
from dataclasses import dataclass, field
from typing import Annotated, Any, Callable

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import Field

from .backend import Backend

MAX_RESULTS = 10
HOLD_TOKEN_TTL_S = 120


@dataclass
class AssociateServer:
    mcp: FastMCP
    audit: list[dict] = field(default_factory=list)


def _first_name_initial(name: str) -> str:
    parts = name.split()
    return parts[0] + (f" {parts[-1][0]}." if len(parts) > 1 else "")


def build_server(backend: Backend, associate_store: str, write_scope: bool = False,
                 clock: Callable[[], float] = time.time) -> AssociateServer:
    mcp = FastMCP("kestrel-associate")
    srv = AssociateServer(mcp=mcp)
    tokens: dict[str, dict] = {}

    def audited(name: str, args: dict, fn: Callable[[], Any]) -> Any:
        try:
            out = fn()
        except ToolError as e:
            srv.audit.append({"tool": name, "args": args, "ok": False, "error": str(e), "at": clock()})
            raise
        srv.audit.append({"tool": name, "args": args, "ok": True, "at": clock()})
        return out

    def require_sku(sku: str) -> dict:
        p = backend.products.get(sku)
        if p is None:
            raise ToolError(f"Unknown SKU {sku}. Use find_product to look up the SKU first.")
        return p

    @mcp.tool()
    def find_product(
        query: Annotated[str, Field(min_length=2, max_length=100, description="Words in the product name, e.g. 'ridgeline tent'")],
        limit: Annotated[int, Field(ge=1, le=MAX_RESULTS, description="How many results, 1-10")] = 5,
    ) -> dict:
        """Find products by name words. Returns SKU, name, price and aisle for each match.
        Use the SKU with store_stock or prepare_hold."""
        def run() -> dict:
            hits = backend.search(query)
            items = [{"sku": p["sku"], "name": p["name"], "price": f"${p['price_cents'] / 100:.2f}", "aisle": p["aisle"]}
                     for p in hits[:limit]]
            out: dict = {"results": items, "more_results": len(hits) > limit}
            if out["more_results"]:
                out["hint"] = f"{len(hits) - limit} more matches: add words to the query or raise limit (max {MAX_RESULTS})."
            return out
        return audited("find_product", {"query": query, "limit": limit}, run)

    @mcp.tool()
    def store_stock(
        sku: Annotated[str, Field(description="Kestrel SKU, e.g. KO-TENT-2P")],
        store_id: Annotated[str | None, Field(pattern=r"^[0-9]{3}$", description="3-digit store id; default: your store")] = None,
    ) -> dict:
        """Units available now for one SKU at a store (your store unless store_id is given)."""
        def run() -> dict:
            require_sku(sku)
            st = store_id or associate_store
            return {"sku": sku, "store_id": st, "available": backend.available(sku, st)}
        return audited("store_stock", {"sku": sku, "store_id": store_id}, run)

    @mcp.tool()
    def order_lookup(order_id: Annotated[str, Field(pattern=r"^K-[0-9]{4}$", description="Order id, e.g. K-5501")]) -> dict:
        """Status of a pickup order at your store: status, items and the customer's first name to greet them."""
        def run() -> dict:
            o = backend.orders.get(order_id)
            if o is None or o["store_id"] != associate_store:
                raise ToolError(f"No pickup order {order_id} at store {associate_store}. Check the id on the customer's receipt.")
            return {"order_id": o["order_id"], "status": o["status"], "items": o["items"],
                    "customer": _first_name_initial(o["customer"]["name"])}
        return audited("order_lookup", {"order_id": order_id}, run)

    if write_scope:
        @mcp.tool()
        def prepare_hold(
            sku: Annotated[str, Field(description="Kestrel SKU")],
            customer_name: Annotated[str, Field(min_length=1, max_length=60)],
            quantity: Annotated[int, Field(ge=1, le=5)] = 1,
        ) -> dict:
            """Step 1 of 2: check a hold at your store and get a confirmation token. Nothing is held yet:
            read the summary to the associate, then call hold_item_for_customer with the token."""
            def run() -> dict:
                p = require_sku(sku)
                avail = backend.available(sku, associate_store)
                if quantity > avail:
                    raise ToolError(f"Only {avail} of {sku} available at store {associate_store}; lower the quantity.")
                tok = "hold_" + secrets.token_urlsafe(10)
                tokens[tok] = {"sku": sku, "customer_name": customer_name, "quantity": quantity,
                               "expires_at": clock() + HOLD_TOKEN_TTL_S}
                return {"confirmation_token": tok, "expires_in_s": HOLD_TOKEN_TTL_S,
                        "summary": f"Hold {quantity} x {p['name']} at store {associate_store} for {customer_name}."}
            return audited("prepare_hold", {"sku": sku, "customer_name": customer_name, "quantity": quantity}, run)

        @mcp.tool()
        def hold_item_for_customer(confirmation_token: Annotated[str, Field(min_length=6)]) -> dict:
            """Step 2 of 2: place the hold prepared by prepare_hold. The token is single use and expires."""
            def run() -> dict:
                t = tokens.pop(confirmation_token, None)
                if t is None:
                    raise ToolError("Unknown or already used confirmation_token. Call prepare_hold again.")
                if clock() > t["expires_at"]:
                    raise ToolError("confirmation_token expired. Call prepare_hold again.")
                if t["quantity"] > backend.available(t["sku"], associate_store):
                    raise ToolError("Stock changed since prepare_hold. Call prepare_hold again.")
                return backend.place_hold(t["sku"], associate_store, t["customer_name"], t["quantity"])
            return audited("hold_item_for_customer", {"confirmation_token": confirmation_token[:10] + "..."}, run)

    @mcp.resource("kestrel://stores/{store_id}/hours")
    def store_hours(store_id: str) -> str:
        """Opening hours of a Kestrel store."""
        return backend.hours.get(store_id, "unknown store")

    return srv
