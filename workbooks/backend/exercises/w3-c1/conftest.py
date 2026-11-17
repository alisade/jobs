"""Fixtures shared by visible and hidden tests (root conftest so both directories see them)."""
import httpx
import pytest

from app.directory import Directory
from app.main import create_app
from testkit import Clock


@pytest.fixture()
def clock():
    return Clock()


@pytest.fixture()
async def svc(tmp_path, clock):
    directory = Directory(latency=0.02)
    app = create_app(str(tmp_path / "accounts.db"), directory=directory, clock=clock)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://accounts-svc") as client:
            yield client, app
