from __future__ import annotations

import json
import sys
from pathlib import Path

import anyio
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from grcmcp.server import build_server  # noqa: E402
from grcmcp.store import GrcStore  # noqa: E402

ENG = "ENG-2026-SOX-ITGC"
KEY = b"test-review-service-key-0f3a"
NOW = 1_793_000_000.0


class Harness:
    """Synchronous wrapper around the in-memory MCP client (each call opens a session; bounded)."""

    def __init__(self, server):
        self.server = server

    def _run(self, fn):
        async def go():
            from mcp.client.client import Client
            with anyio.fail_after(20):
                async with Client(self.server) as c:
                    return await fn(c)
        return anyio.run(go)

    def tools(self):
        return self._run(lambda c: c.list_tools()).tools

    def call(self, name, args=None):
        r = self._run(lambda c: c.call_tool(name, args or {}))
        text = r.content[0].text if r.content else ""
        data = None
        if not r.is_error:
            try:
                data = json.loads(text)
            except ValueError:
                data = None
        return r.is_error, data, text


@pytest.fixture
def store():
    return GrcStore()


@pytest.fixture
def mcp(store):
    return Harness(build_server(store, engagement=ENG, approval_key=KEY, preparer="ralvarez", now=lambda: NOW))
