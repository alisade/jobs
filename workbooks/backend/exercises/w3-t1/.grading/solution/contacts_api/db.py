"""Schema and engine for the contacts read path. SQLite (aiosqlite) stands in for Postgres here:
the bug and the fix are about the query, not the engine."""

from __future__ import annotations

from sqlalchemy import Column, Index, MetaData, String, Table
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

metadata = MetaData()

contacts = Table(
    "contacts",
    metadata,
    Column("id", String(36), primary_key=True),
    Column("tenant_id", String(40), nullable=False),
    Column("account_id", String(36), nullable=True),
    Column("email", String(320), nullable=False),
    Column("full_name", String(200), nullable=False),
    # ISO-8601 UTC with microseconds, e.g. 2026-11-02T03:00:00.000000Z (sorts lexically)
    Column("created_at", String(32), nullable=False),
    Index("contacts_tenant_created_id_idx", "tenant_id", "created_at", "id"),
)


def make_engine(url: str) -> AsyncEngine:
    return create_async_engine(url)


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
