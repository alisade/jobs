"""check_inventory tool for the shopping assistant.

Release 2026.11.18 changed this tool from "the first 3 products in the answer" to "every product in
the answer", so the assistant can say which of the suggested items are in stock nearby.
"""

from __future__ import annotations

from .catalog_client import CatalogClient, CatalogError

PER_CALL_TIMEOUT_S = 2.0


class ToolError(Exception):
    """Returned to the model as an is_error tool result."""


async def check_inventory(
    catalog: CatalogClient,
    skus: list[str],
    stores: list[str],
    deadline_s: float | None = None,
) -> dict:
    """Stock for every (sku, store) pair, in input order.

    Returns {"items": [{"sku", "store_id", "available", "stock_unknown"}], "partial": bool}.
    deadline_s is the time this tool may still spend (the request's remaining budget).
    """
    items = []
    for sku in skus:
        for store in stores:
            try:
                n = await catalog.get_stock(sku, store, timeout=PER_CALL_TIMEOUT_S)
            except CatalogError as e:
                raise ToolError(f"inventory lookup failed for {sku} at {store}: {e}") from e
            items.append({"sku": sku, "store_id": store, "available": n, "stock_unknown": False})
    return {"items": items, "partial": False}
