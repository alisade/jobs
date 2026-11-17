"""Idempotency-Key handling for side-effecting POSTs.

Clients (other teams' services, workflow activities, agents) retry on timeouts and 5xx. A retry
with the same Idempotency-Key must not create a second record; it must get the original response.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import select

from .models import IdempotencyKey

Handler = Callable[[], Awaitable[tuple[int, dict]]]


async def run_idempotent(request: Request, tenant_id: str, handler: Handler) -> Response:
    """Run `handler` at most once per (tenant, Idempotency-Key) and replay its response on retries."""
    sm = request.app.state.sessionmaker
    key = request.headers.get("Idempotency-Key")
    if key is None:
        status, body = await handler()
        return JSONResponse(body, status_code=status)

    async with sm() as s:
        row = await s.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id == tenant_id, IdempotencyKey.key == key))
    if row is not None and row.status == "completed":
        return JSONResponse(json.loads(row.response_body), status_code=row.response_code,
                            headers={"Idempotent-Replayed": "true"})

    status, body = await handler()

    async with sm() as s:
        await s.merge(IdempotencyKey(tenant_id=tenant_id, key=key, fingerprint="", status="completed",
                                     response_code=status, response_body=json.dumps(body),
                                     created_at=datetime.now(timezone.utc)))
        await s.commit()
    return JSONResponse(body, status_code=status)
