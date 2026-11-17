"""GET /v1/contacts: the page the marketing partner sync walks every 15 minutes."""

from __future__ import annotations

from fastapi import FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncEngine

from . import pagination
from .problems import Problem


def contact_json(row) -> dict:
    return {"id": row.id, "account_id": row.account_id, "email": row.email,
            "full_name": row.full_name, "created_at": row.created_at}


def create_app(engine: AsyncEngine) -> FastAPI:
    app = FastAPI(title="accounts-svc contacts read API")

    @app.exception_handler(Problem)
    async def _problem(request: Request, exc: Problem):
        return exc.response(str(request.url.path))

    @app.get("/v1/contacts")
    async def list_contacts(request: Request, limit: int | None = None, cursor: str | None = None):
        tenant = request.headers.get("x-tenant-id")
        if not tenant:
            raise Problem(400, "missing-tenant", "X-Tenant-Id header is required")
        n = pagination.clamp_limit(limit)
        async with engine.connect() as conn:
            rows = (await conn.execute(pagination.page_query(tenant, cursor, n))).fetchall()
        next_cursor = pagination.encode_cursor(rows[-1]) if len(rows) == n else None
        return {"data": [contact_json(r) for r in rows], "next_cursor": next_cursor}

    return app
