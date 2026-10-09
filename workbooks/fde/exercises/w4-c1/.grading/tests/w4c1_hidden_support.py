"""Helpers shared by the visible tests: an in-memory MCP client session on the server."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager

from mcp.shared.memory import create_connected_server_and_client_session

from trust_advisor.server import build_server
from trust_advisor.store import DecisionStore

GOOD_POLICY = """\
cart:
  timeout_ms: 150
  on_failure: open
checkout:
  timeout_ms: 400
  on_failure: closed
breaker:
  failures: 5
  reset_s: 30
"""


@asynccontextmanager
async def client(**kwargs):
    async with create_connected_server_and_client_session(build_server(**kwargs)) as session:
        yield session


async def call(session, name, args=None):
    """(isError, structured content or None, text of the first content block)."""
    result = await session.call_tool(name, args or {})
    text = result.content[0].text if result.content else ""
    # A tool that is not registered also comes back as an error result; that is not the
    # validation the tests are asking for.
    assert "Unknown tool" not in text, f"tool {name} is not registered"
    return result.isError, result.structuredContent, text


def raw_store() -> DecisionStore:
    return DecisionStore.from_jsonl()


def dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True)
