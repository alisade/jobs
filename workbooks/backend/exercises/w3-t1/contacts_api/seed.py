"""Deterministic seed data shaped like the bulk import of 2026-11-02 (used by tests and make repro)."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import insert

from .db import contacts

IMPORT_TS = "2026-11-02T03:00:00.000000Z"


def ts(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def make_rows(tenant: str, organic: int, bulk: int, seed: int = 44) -> list[dict]:
    rng = random.Random(seed)
    base = datetime(2026, 10, 1, tzinfo=timezone.utc)
    rows = []
    for i in range(organic):
        created = base + timedelta(seconds=rng.randint(0, 40 * 86400), microseconds=rng.randint(0, 999999))
        rows.append(_row(rng, tenant, ts(created), i))
    for i in range(bulk):  # the bulk import: one statement, one now() -> identical created_at
        rows.append(_row(rng, tenant, IMPORT_TS, organic + i))
    rng.shuffle(rows)
    return rows


def _row(rng: random.Random, tenant: str, created_at: str, n: int) -> dict:
    rid = "%08x-%04x-4%03x-a%03x-%012x" % (rng.getrandbits(32), rng.getrandbits(16), rng.getrandbits(12),
                                          rng.getrandbits(12), rng.getrandbits(48))
    return {"id": rid, "tenant_id": tenant, "account_id": None, "email": f"contact{n}@{tenant}.example",
            "full_name": f"Contact {n}", "created_at": created_at}


async def seed(engine, rows: list[dict]) -> None:
    async with engine.begin() as conn:
        for i in range(0, len(rows), 500):
            await conn.execute(insert(contacts), rows[i:i + 500])
