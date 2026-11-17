"""Engine and session factory. SQLite (aiosqlite, WAL) stands in for Postgres in this exercise."""

from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from .models import Base


def make_engine(path: str) -> AsyncEngine:
    engine = create_async_engine(f"sqlite+aiosqlite:///{path}", connect_args={"timeout": 15})

    @event.listens_for(engine.sync_engine, "connect")
    def _pragmas(dbapi_conn, _record):  # noqa: ANN001
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=15000")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    return engine


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker:
    return async_sessionmaker(engine, expire_on_commit=False)
