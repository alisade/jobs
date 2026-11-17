"""change-management MCP server.

TODO (see README): four task-shaped tools with validated inputs, small outputs, read-only
annotations on the read tools, and the caller's identity taken from the verified token, never
from a tool argument.
"""
from __future__ import annotations

from typing import Callable

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .backends import Caller, ChangeStore, Cmdb, verify_token


def build_server(store: ChangeStore, cmdb: Cmdb, caller_token: str,
                 verifier: Callable[[str], Caller] = verify_token) -> MCPServer:
    srv = MCPServer("change-management")

    @srv.tool()
    def create_change(service: str, summary: str, risk: str, window_start: str, requester: str) -> dict:
        """Create a change."""
        c = store.create(service, summary, risk, window_start, requester)
        return c  # TODO: validate, check the CMDB, identity from the token, small output

    @srv.tool()
    def get_change(change_id: str) -> dict:
        """Get a change."""
        return store.get(change_id)  # TODO

    @srv.tool()
    def list_my_open_changes(user: str) -> dict:
        """List changes."""
        return {"changes": store.list_by_requester(user)}  # TODO: identity, open states, pagination

    @srv.tool()
    def add_comment(change_id: str, text: str) -> dict:
        """Comment."""
        raise ToolError("TODO")

    return srv
