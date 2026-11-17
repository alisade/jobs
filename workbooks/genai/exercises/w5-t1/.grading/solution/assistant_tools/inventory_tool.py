"""check_inventory tool for the shopping assistant. Reference solution.

One batch call per 50 (sku, store) pairs instead of one sequential call per pair, at most
MAX_CONCURRENCY batches in flight, every call bounded by the request's remaining budget, and partial
results (stock unknown) instead of an error when the deadline or a batch fails.
"""

from __future__ import annotations

import asyncio

from .catalog_client import BATCH_MAX, CatalogClient, CatalogError

PER_CALL_TIMEOUT_S = 0.8
DEFAULT_BUDGET_S = 3.0
MAX_CONCURRENCY = 4


class ToolError(Exception):
    """Returned to the model as an is_error tool result."""


def _unique_pairs(skus: list[str], stores: list[str]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for sku in skus:
        for store in stores:
            p = (sku, store)
            if p not in seen:
                seen.add(p)
                out.append(p)
    return out


async def check_inventory(
    catalog: CatalogClient,
    skus: list[str],
    stores: list[str],
    deadline_s: float | None = None,
) -> dict:
    """Stock for every (sku, store) pair, in input order (duplicates removed).

    Returns {"items": [{"sku", "store_id", "available", "stock_unknown"}], "partial": bool}.
    deadline_s is the time this tool may still spend (the request's remaining budget).
    """
    wanted = _unique_pairs(skus, stores)
    if not wanted:
        return {"items": [], "partial": False}
    loop = asyncio.get_running_loop()
    budget = DEFAULT_BUDGET_S if deadline_s is None else max(0.0, deadline_s)
    end = loop.time() + budget
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    found: dict[tuple[str, str], int] = {}

    async def one(chunk: list[tuple[str, str]]) -> None:
        async with sem:
            remaining = end - loop.time()
            if remaining <= 0.005:
                return
            try:
                found.update(await catalog.batch_stock(chunk, timeout=min(PER_CALL_TIMEOUT_S, remaining)))
            except (CatalogError, asyncio.TimeoutError):
                return  # this chunk stays unknown; the others still count

    chunks = [wanted[i:i + BATCH_MAX] for i in range(0, len(wanted), BATCH_MAX)]
    tasks = [asyncio.ensure_future(one(c)) for c in chunks]
    try:
        # belt and braces: never outlive the budget even if a client ignores its timeout
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=budget + 0.05)
    except asyncio.TimeoutError:
        for t in tasks:
            t.cancel()

    items = []
    for sku, store in wanted:
        n = found.get((sku, store))
        items.append({"sku": sku, "store_id": store, "available": n, "stock_unknown": n is None})
    return {"items": items, "partial": any(i["stock_unknown"] for i in items)}
