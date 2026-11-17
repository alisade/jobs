"""API contract models (complete). The OpenAPI document and the TypeScript types come from these."""

from __future__ import annotations

from pydantic import BaseModel, Field

PROBLEM_BASE = "https://api.kestrel.example/problems/"


class Health(BaseModel):
    status: str


class ProductSummary(BaseModel):
    sku: str
    name: str
    category: str
    price_cents: int


class ProductPage(BaseModel):
    items: list[ProductSummary]
    next_cursor: str | None = Field(None, description="Pass as `cursor` to get the next page; null on the last page.")


class StoreStock(BaseModel):
    store_id: str
    available: int


class ProductDetail(BaseModel):
    sku: str
    name: str
    description: str
    category: str
    price_cents: int
    stock: list[StoreStock]


class ReservationRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=32)
    store_id: str = Field(..., pattern=r"^[0-9]{3}$")
    quantity: int = Field(..., ge=1, le=10)


class ReservationCreated(BaseModel):
    reservation_id: str
    sku: str
    store_id: str
    quantity: int
    available_after: int


class Problem(BaseModel):
    """RFC 9457 problem details."""

    type: str
    title: str
    status: int
    detail: str
