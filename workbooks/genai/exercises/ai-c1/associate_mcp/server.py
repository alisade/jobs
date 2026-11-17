"""MCP server for Kestrel store associates (prototype).

The prototype was generated straight from the store REST API: one tool per endpoint, full records,
and the write tool always on. See README.md for what the platform review asked for.
"""


import time
from dataclasses import dataclass, field
from typing import Callable

from mcp.server.fastmcp import FastMCP

from .backend import Backend

MAX_RESULTS = 10
HOLD_TOKEN_TTL_S = 120


@dataclass
class AssociateServer:
    mcp: FastMCP
    audit: list[dict] = field(default_factory=list)


def build_server(backend: Backend, associate_store: str, write_scope: bool = False,
                 clock: Callable[[], float] = time.time) -> AssociateServer:
    mcp = FastMCP("kestrel-associate")
    srv = AssociateServer(mcp=mcp)

    @mcp.tool()
    def find_product(query: str) -> list[dict]:
        """GET /products?q="""
        return backend.search(query)

    @mcp.tool()
    def store_stock(sku: str, store_id: str) -> int:
        """GET /stock"""
        return backend.available(sku, store_id)

    @mcp.tool()
    def order_lookup(order_id: str) -> dict:
        """GET /orders/{id}"""
        return backend.orders[order_id]

    @mcp.tool()
    def hold_item_for_customer(sku: str, customer_name: str, quantity: int = 1) -> dict:
        """POST /holds"""
        return backend.place_hold(sku, associate_store, customer_name, quantity)

    # TODO: everything in README.md "Requirements"

    return srv
