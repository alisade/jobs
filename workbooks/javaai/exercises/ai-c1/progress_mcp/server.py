"""Learner-progress MCP server used by the tutor agent (ADK McpToolset over stdio or streamable HTTP).

TODO(ai-c1): this is the first draft, a 1:1 copy of the REST API. See README "Requirements".
"""

# No "from __future__ import annotations" here: FastMCP reads the real annotation objects.
from mcp.server.fastmcp import FastMCP

from .catalog_api import CatalogApi


def build_server(api: CatalogApi, learner_id: str) -> FastMCP:
    """One server instance per tutor session; learner_id is the authenticated session's learner."""
    mcp = FastMCP("kestrel-learner-progress")

    @mcp.tool()
    def get_progress(learner_id: str, course_id: str) -> dict:
        return api.progress(learner_id, course_id)

    @mcp.tool()
    def get_lessons(course_id: str) -> list:
        return api.lessons(course_id)

    @mcp.tool()
    def get_lesson(lesson_id: str) -> dict:
        return api.lesson(lesson_id) or {}

    @mcp.tool()
    def record_mastery(learner_id: str, lesson_id: str) -> dict:
        return api.record_mastery(learner_id, lesson_id)

    return mcp


if __name__ == "__main__":  # stdio transport for Claude Code / ADK McpToolset(StdioServerParameters(...))
    import os
    build_server(CatalogApi(), os.environ.get("KESTREL_LEARNER_ID", "lrn-ada")).run()
