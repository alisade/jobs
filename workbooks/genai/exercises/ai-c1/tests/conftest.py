import asyncio
import json
import logging

from mcp.shared.memory import create_connected_server_and_client_session

from associate_mcp.backend import Backend
from associate_mcp.server import build_server

logging.getLogger("mcp").setLevel(logging.WARNING)


class Clock:
    def __init__(self, t: float = 1000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


def session_run(srv, fn, timeout: float = 10.0):
    """Open an in-memory MCP client session to srv and run `await fn(session)`."""

    async def go():
        async with create_connected_server_and_client_session(srv.mcp._mcp_server) as s:
            return await fn(s)

    return asyncio.run(asyncio.wait_for(go(), timeout))


def payload(result):
    """Decode a CallToolResult's first text block as JSON (or return the raw text)."""
    t = result.content[0].text
    try:
        return json.loads(t)
    except ValueError:
        return t


def make(write_scope=False, store="012"):
    backend, clock = Backend(), Clock()
    return build_server(backend, store, write_scope=write_scope, clock=clock), backend, clock
