"""Shared fixtures for visible and hidden tests (root conftest so both directories see them)."""
import pytest_asyncio
import httpx

from contacts_api.db import create_schema, make_engine
from contacts_api.main import create_app


@pytest_asyncio.fixture
async def make_client(tmp_path):
    engines = []

    async def factory(rows):
        from contacts_api.seed import seed
        engine = make_engine(f"sqlite+aiosqlite:///{tmp_path}/c{len(engines)}.db")
        engines.append(engine)
        await create_schema(engine)
        await seed(engine, rows)
        app = create_app(engine)
        return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://svc"), engine

    yield factory
    for e in engines:
        await e.dispose()
