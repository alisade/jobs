"""Idempotency-Key handling for side-effecting POSTs.

Clients (other teams' services, workflow activities, agents) retry on timeouts and 5xx. A retry
with the same Idempotency-Key must not create a second record; it must get the original response.

Protocol (per tenant and key):
1. Claim the key by INSERTing a row with status in_progress. The primary key (tenant_id, key) makes
   the claim atomic: exactly one concurrent request wins, the others get an IntegrityError.
2. Losers read the existing row: different fingerprint -> 422; still in_progress -> 409 + Retry-After;
   completed -> replay the stored response with Idempotent-Replayed: true. Rows older than the
   retention window are deleted and the claim is retried, so an expired key behaves like a new one.
3. The winner runs the handler. On an exception or a 5xx it deletes the row (releases the key) so a
   retry can run; otherwise it stores the response and marks the row completed.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from .models import IdempotencyKey
from .problems import PROBLEM_JSON, ProblemError

Handler = Callable[[], Awaitable[tuple[int, dict]]]
RETENTION = timedelta(hours=24)
MAX_KEY_LEN = 255


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


async def fingerprint(request: Request) -> str:
    raw = await request.body()
    try:
        canonical = json.dumps(json.loads(raw or b"null"), sort_keys=True, separators=(",", ":"))
    except ValueError:
        canonical = raw.decode("utf-8", "replace")
    h = hashlib.sha256()
    h.update(f"{request.method} {request.url.path}\n".encode())
    h.update(canonical.encode())
    return h.hexdigest()


def _response(status: int, body: dict, replayed: bool = False) -> JSONResponse:
    headers = {"Idempotent-Replayed": "true"} if replayed else None
    media = PROBLEM_JSON if status >= 400 else "application/json"
    return JSONResponse(body, status_code=status, headers=headers, media_type=media)


async def _claim(sm, tenant_id: str, key: str, fp: str, now: datetime) -> IdempotencyKey | None:
    """Try to claim the key. Returns None when claimed, or the existing row when someone else has it."""
    for _ in range(3):
        try:
            async with sm() as s, s.begin():
                s.add(IdempotencyKey(tenant_id=tenant_id, key=key, fingerprint=fp, status="in_progress",
                                     created_at=now))
            return None
        except IntegrityError:
            pass
        async with sm() as s:
            row = await s.scalar(select(IdempotencyKey).where(IdempotencyKey.tenant_id == tenant_id,
                                                              IdempotencyKey.key == key))
        if row is None:
            continue  # released between our insert and our read: try again
        if now - _aware(row.created_at) > RETENTION:
            async with sm() as s, s.begin():
                await s.execute(delete(IdempotencyKey).where(IdempotencyKey.tenant_id == tenant_id,
                                                             IdempotencyKey.key == key,
                                                             IdempotencyKey.created_at == row.created_at))
            continue
        return row
    raise ProblemError(409, "Idempotency key is busy", "retry shortly", type_="idempotency-in-progress",
                       headers={"Retry-After": "1"})


async def run_idempotent(request: Request, tenant_id: str, handler: Handler) -> Response:
    """Run `handler` at most once per (tenant, Idempotency-Key) and replay its response on retries."""
    sm = request.app.state.sessionmaker
    key = request.headers.get("Idempotency-Key")
    if not key:
        raise ProblemError(400, "Idempotency-Key header is required",
                           "every POST must carry a unique Idempotency-Key", type_="idempotency-key-missing")
    if len(key) > MAX_KEY_LEN:
        raise ProblemError(400, "Idempotency-Key is too long", f"at most {MAX_KEY_LEN} characters",
                           type_="idempotency-key-invalid")
    fp = await fingerprint(request)
    now = _aware(request.app.state.clock())

    existing = await _claim(sm, tenant_id, key, fp, now)
    if existing is not None:
        if existing.fingerprint != fp:
            raise ProblemError(422, "Idempotency-Key reused with a different request",
                               "use a new key for a different request", type_="idempotency-key-mismatch")
        if existing.status != "completed":
            raise ProblemError(409, "A request with this Idempotency-Key is in progress",
                               "retry after the original request finishes", type_="idempotency-in-progress",
                               headers={"Retry-After": "1"})
        return _response(existing.response_code, json.loads(existing.response_body), replayed=True)

    where = (IdempotencyKey.tenant_id == tenant_id, IdempotencyKey.key == key)
    try:
        status, body = await handler()
    except BaseException:
        async with sm() as s, s.begin():
            await s.execute(delete(IdempotencyKey).where(*where))
        raise
    async with sm() as s, s.begin():
        if status >= 500:
            await s.execute(delete(IdempotencyKey).where(*where))
        else:
            await s.execute(update(IdempotencyKey).where(*where).values(
                status="completed", response_code=status, response_body=json.dumps(body)))
    return _response(status, body)
