"""Kestrel catalog service: products, stock and reservations.

Prototype from the catalog team's hack week. It runs, but it does not meet the contract in README.md.
Every TODO below is part of your task.
"""


from typing import Annotated, Iterator

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .db import Base, Inventory, Product, make_engine, make_sessionmaker, seed
from .schemas import ProductDetail, ProductSummary, StoreStock

MAX_PAGE = 50


def create_app(engine=None) -> FastAPI:
    engine = engine or make_engine()
    Base.metadata.create_all(engine)
    SessionLocal = make_sessionmaker(engine)
    with SessionLocal() as s:
        if s.scalar(select(func.count()).select_from(Product)) == 0:
            seed(s)

    app = FastAPI(title="Kestrel Catalog API", version="1.2.0")

    def get_session() -> Iterator[Session]:
        with SessionLocal() as s:
            yield s

    SessionDep = Annotated[Session, Depends(get_session)]

    # TODO: problem+json error responses (RFC 9457) for the 400/404/409/422 cases in README.md,
    # declared in the OpenAPI document so the TypeScript client gets the Problem type.

    @app.get("/healthz", operation_id="health")
    def health() -> dict:
        return {"status": "ok"}

    # TODO: operation_id="listProducts", response_model=ProductPage, case-insensitive q,
    # max_price_cents and in_stock_at filters, cursor pagination with a stable order
    # (price_cents, then sku), limit capped at MAX_PAGE.
    @app.get("/products")
    def list_products(
        session: SessionDep,
        q: str | None = None,
        category: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ProductSummary]:
        stmt = select(Product)
        if q:
            stmt = stmt.where(or_(Product.name.contains(q), Product.description.contains(q)))
        if category:
            stmt = stmt.where(Product.category == category)
        stmt = stmt.order_by(Product.price_cents).offset(offset).limit(limit)
        return [
            ProductSummary(sku=p.sku, name=p.name, category=p.category, price_cents=p.price_cents)
            for p in session.scalars(stmt)
        ]

    # TODO: operation_id="getProduct"; 404 as problem+json; available = on_hand - reserved
    @app.get("/products/{sku}", response_model=ProductDetail)
    def get_product(sku: str, session: SessionDep) -> ProductDetail:
        p = session.get(Product, sku)
        if p is None:
            raise HTTPException(404)
        inv = session.scalars(select(Inventory).where(Inventory.sku == sku))
        return ProductDetail(
            sku=p.sku, name=p.name, description=p.description, category=p.category,
            price_cents=p.price_cents,
            stock=[StoreStock(store_id=i.store_id, available=i.on_hand) for i in inv],
        )

    # TODO: POST /inventory/reservations, operation_id="createReservation", 201, Idempotency-Key
    # header, 409 when stock is short, safe replay of the same key (see README.md).

    return app


app = create_app()
