"""GRC MCP server for ControlPilot: read-only tools over one engagement, plus one gated write.
TODO: README tasks 1, 2 and 4. list_controls is done as the pattern to follow."""

from __future__ import annotations

import time
from typing import Callable

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError  # noqa: F401  raise this for errors the model should see
from mcp_types import ToolAnnotations

from .store import GrcStore
from .tokens import ApprovalError, verify_approval  # noqa: F401

READ = ToolAnnotations(readOnlyHint=True, openWorldHint=False)


def build_server(store: GrcStore, *, engagement: str, approval_key: bytes, preparer: str,
                 now: Callable[[], float] = time.time) -> MCPServer:
    eng = store.engagement(engagement)
    server = MCPServer("mfh-grc", instructions=f"GRC data for engagement {engagement} only ({eng['name']}).")

    @server.tool(annotations=READ, description=(
        "List the controls in scope for this audit engagement: control_id, name, frequency and owner. "
        "Call this first to get valid control_id values for the other tools."))
    def list_controls() -> dict:
        return {"engagement": engagement, "controls": eng["controls"]}

    # TODO: get_control_test(control_id)
    # TODO: search_exceptions(query="", status=None, cursor=None, limit=10)
    # TODO: get_evidence_index(control_id, sample_id)
    # TODO: record_exception(control_id, sample_id, description, approval_token)

    return server
