"""Stand-in for ADK's McpToolset: connects to an MCP server and exposes its tools to an agent.
Like the real one, `tool_filter=None` means every tool the server lists. Do not change."""

from __future__ import annotations

from .backend import SERVER_TOOLS


class McpToolset:
    def __init__(self, tool_filter: list[str] | None = None):
        self.tool_filter = tool_filter

    def get_tools(self) -> dict:
        if self.tool_filter is None:
            return dict(SERVER_TOOLS)
        return {k: v for k, v in SERVER_TOOLS.items() if k in self.tool_filter}
