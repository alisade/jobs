"""catalog-search: the product search API behind the storefront and the shopping assistant.

Release 2026.11.04 added promotion badges to search results (see evidence/release-notes.md).
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, Query

from .data import search_rows
from .promotions_sdk import PromotionsClient

app = FastAPI(title="catalog-search", version="2026.11.04")

_promotions = PromotionsClient()


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
    badges = promotions.badges_for([r["sku"] for r in rows])
    for r in rows:
        if r["sku"] in badges:
            r["badge"] = badges[r["sku"]]
    return {"query": q, "count": len(rows), "results": rows}
