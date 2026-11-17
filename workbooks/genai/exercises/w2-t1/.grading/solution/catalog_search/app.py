"""catalog-search: the product search API behind the storefront and the shopping assistant.

Fixed: the blocking promotions SDK runs in the threadpool with a bounded timeout, and search
degrades to results without badges instead of failing or stalling the event loop.
"""

from __future__ import annotations

import logging
import os

from fastapi import Depends, FastAPI, Query
from fastapi.concurrency import run_in_threadpool

from .data import search_rows
from .promotions_sdk import PromotionsClient, PromotionsError

log = logging.getLogger("catalog-search")

app = FastAPI(title="catalog-search", version="2026.11.05")

_promotions = PromotionsClient()
PROMO_TIMEOUT_S = float(os.environ.get("PROMO_TIMEOUT_S", "0.3"))


def get_promotions() -> PromotionsClient:
    return _promotions


@app.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok"}


@app.get("/search")
async def search(
    q: str = Query(..., min_length=1, max_length=200),
    category: str | None = None,
    limit: int = Query(20, ge=1, le=50),
    promotions: PromotionsClient = Depends(get_promotions),
) -> dict:
    rows = search_rows(q, category, limit)
    degraded = False
    badges: dict[str, str] = {}
    if rows:
        try:
            # The SDK blocks its thread; never call it on the event loop thread.
            badges = await run_in_threadpool(promotions.badges_for, [r["sku"] for r in rows], PROMO_TIMEOUT_S)
        except PromotionsError as e:
            degraded = True
            log.warning("promotions degraded: %s", e)
    for r in rows:
        if r["sku"] in badges:
            r["badge"] = badges[r["sku"]]
    return {"query": q, "count": len(rows), "results": rows, "promotions_degraded": degraded}
