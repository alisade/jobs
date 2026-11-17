"""Kestrel catalog service: products, stock and reservations. Reference solution."""


import base64
import hashlib
import json
from typing import Annotated, Iterator

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import Base, Inventory, Product, Reservation, make_engine, make_sessionmaker, seed
from .schemas import (
    PROBLEM_BASE,
    Health,
    Problem,
    ProductDetail,
    ProductPage,
    ProductSummary,
    ReservationCreated,
    ReservationRequest,
    StoreStock,
)

MAX_PAGE = 50
PROBLEM_JSON = "application/problem+json"
PROBLEM_RESPONSES = {
    "model": Problem,
    "content": {PROBLEM_JSON: {"schema": {"$ref": "#/components/schemas/Problem"}}},
}


class ProblemError(Exception):
    def __init__(self, status: int, slug: str, title: str, detail: str) -> None:
        self.status, self.slug, self.title, self.detail = status, slug, title, detail


def _encode_cursor(price: int, sku: str) -> str:
    return base64.urlsafe_b64encode(json.dumps([price, sku]).encode()).decode()


def _decode_cursor(cursor: str) -> tuple[int, str]:
    try:
        price, sku = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        return int(price), str(sku)
    except Exception as e:  # noqa: BLE001
        raise ProblemError(400, "invalid-cursor", "Invalid cursor", "cursor is not one this API issued") from e


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

    @app.exception_handler(ProblemError)
    async def _problem(_: Request, e: ProblemError) -> JSONResponse:
        body = Problem(type=PROBLEM_BASE + e.slug, title=e.title, status=e.status, detail=e.detail)
        return JSONResponse(body.model_dump(), status_code=e.status, media_type=PROBLEM_JSON)

    @app.get("/healthz", operation_id="health", response_model=Health)
    def health() -> Health:
        return Health(status="ok")

    @app.get(
        "/products",
        operation_id="listProducts",
        response_model=ProductPage,
        responses={400: PROBLEM_RESPONSES},
    )
    def list_products(
        session: SessionDep,
        q: Annotated[str | None, Query(max_length=100)] = None,
        category: str | None = None,
        max_price_cents: Annotated[int | None, Query(ge=0)] = None,
        in_stock_at: str | None = None,
        limit: Annotated[int, Query(ge=1, le=MAX_PAGE)] = 20,
        cursor: str | None = None,
    ) -> ProductPage:
        stmt = select(Product)
        if q:
            like = f"%{q.lower()}%"
            stmt = stmt.where(or_(func.lower(Product.name).like(like), func.lower(Product.description).like(like)))
        if category:
            stmt = stmt.where(Product.category == category)
        if max_price_cents is not None:
            stmt = stmt.where(Product.price_cents <= max_price_cents)
        if in_stock_at:
            stmt = stmt.join(
                Inventory, and_(Inventory.sku == Product.sku, Inventory.store_id == in_stock_at)
            ).where(Inventory.on_hand - Inventory.reserved > 0)
        if cursor:
            price, sku = _decode_cursor(cursor)
            stmt = stmt.where(
                or_(Product.price_cents > price, and_(Product.price_cents == price, Product.sku > sku))
            )
        stmt = stmt.order_by(Product.price_cents, Product.sku).limit(limit + 1)
        rows = list(session.scalars(stmt))
        more = len(rows) > limit
        rows = rows[:limit]
        items = [ProductSummary(sku=p.sku, name=p.name, category=p.category, price_cents=p.price_cents) for p in rows]
        nxt = _encode_cursor(rows[-1].price_cents, rows[-1].sku) if more and rows else None
        return ProductPage(items=items, next_cursor=nxt)

    @app.get(
        "/products/{sku}",
        operation_id="getProduct",
        response_model=ProductDetail,
        responses={404: PROBLEM_RESPONSES},
    )
    def get_product(sku: str, session: SessionDep) -> ProductDetail:
        p = session.get(Product, sku)
        if p is None:
            raise ProblemError(404, "not-found", "Product not found", f"no product with sku {sku}")
        inv = session.scalars(select(Inventory).where(Inventory.sku == sku).order_by(Inventory.store_id))
        return ProductDetail(
            sku=p.sku,
            name=p.name,
            description=p.description,
            category=p.category,
            price_cents=p.price_cents,
            stock=[StoreStock(store_id=i.store_id, available=i.on_hand - i.reserved) for i in inv],
        )

    @app.post(
        "/inventory/reservations",
        operation_id="createReservation",
        status_code=201,
        response_model=ReservationCreated,
        responses={404: PROBLEM_RESPONSES, 409: PROBLEM_RESPONSES, 422: PROBLEM_RESPONSES},
    )
    def create_reservation(
        body: ReservationRequest,
        session: SessionDep,
        idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=80)],
    ) -> ReservationCreated:
        req_hash = hashlib.sha256(body.model_dump_json().encode()).hexdigest()
        prior = session.scalar(select(Reservation).where(Reservation.idempotency_key == idempotency_key))
        if prior is not None:
            if prior.request_hash != req_hash:
                raise ProblemError(
                    422, "idempotency-key-reused", "Idempotency key reused",
                    "this Idempotency-Key was already used with a different request body",
                )
            return _created(prior)
        inv = session.get(Inventory, (body.sku, body.store_id))
        if inv is None:
            raise ProblemError(404, "not-found", "Product not stocked", f"{body.sku} is not stocked at store {body.store_id}")
        available = inv.on_hand - inv.reserved
        if body.quantity > available:
            raise ProblemError(
                409, "insufficient-stock", "Insufficient stock",
                f"requested {body.quantity}, available {available} at store {body.store_id}",
            )
        inv.reserved += body.quantity
        r = Reservation(
            idempotency_key=idempotency_key, request_hash=req_hash, sku=body.sku,
            store_id=body.store_id, quantity=body.quantity, available_after=available - body.quantity,
        )
        session.add(r)
        try:
            session.commit()
        except IntegrityError:  # a concurrent request with the same key won the race
            session.rollback()
            prior = session.scalar(select(Reservation).where(Reservation.idempotency_key == idempotency_key))
            return _created(prior)
        return _created(r)

    return app


def _created(r: Reservation) -> ReservationCreated:
    return ReservationCreated(
        reservation_id=f"r-{r.id:06d}", sku=r.sku, store_id=r.store_id,
        quantity=r.quantity, available_after=r.available_after,
    )


app = create_app()
