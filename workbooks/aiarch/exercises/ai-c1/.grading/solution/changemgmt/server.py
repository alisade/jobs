"""change-management MCP server.

Identity: one server instance per authenticated MCP session. ``build_server`` verifies the
caller's token once (in production: the bearer token on the Streamable HTTP connection, already
checked by AgentCore Gateway or by the server's own JWT validation) and the tools close over the
verified Caller. No tool takes a requester or user argument, so the model cannot choose who it
acts as.
"""
from __future__ import annotations

import base64
import datetime as dt
import difflib
from typing import Annotated, Callable, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations
from pydantic import Field

from .backends import OPEN_STATES, Caller, ChangeStore, Cmdb, verify_token

PAGE_SIZE = 5
ChangeId = Annotated[str, Field(pattern=r"^CHG-\d{5}$", description="Change id, e.g. CHG-10002")]


def _cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(f"o:{offset}".encode()).decode()


def _offset(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        if not raw.startswith("o:"):
            raise ValueError
        return int(raw[2:])
    except (ValueError, UnicodeDecodeError) as e:
        raise ToolError("invalid cursor: pass back the next_cursor value from the previous page unchanged") from e


def _summary(c: dict) -> dict:
    return {"change_id": c["id"], "service": c["service"], "summary": c["summary"], "risk": c["risk"],
            "state": c["state"], "window_start": c["window_start"]}


def build_server(store: ChangeStore, cmdb: Cmdb, caller_token: str,
                 verifier: Callable[[str], Caller] = verify_token) -> MCPServer:
    caller = verifier(caller_token)  # raises before any tool exists
    srv = MCPServer("change-management", instructions="Create, read and comment on change tickets for the signed-in user.")

    def _load(change_id: str) -> dict:
        c = store.get(change_id)
        if c is None:
            raise ToolError(f"no change {change_id}; use list_my_open_changes to find your changes")
        return c

    @srv.tool()
    def create_change(
        service: Annotated[str, Field(description="CMDB service name, e.g. claims-intake")],
        summary: Annotated[str, Field(min_length=10, max_length=200, description="What changes, 10-200 characters")],
        risk: Literal["low", "medium", "high"],
        window_start: Annotated[dt.datetime, Field(description="Maintenance window start, ISO 8601 with timezone")],
    ) -> dict:
        """Open a draft change for the signed-in user on a CMDB service. High-risk changes need a
        window at least 48 hours ahead. Returns the change id and the approver group."""
        svc = cmdb.lookup(service)
        if svc is None:
            close = difflib.get_close_matches(service, cmdb.names(), n=3)
            hint = f" Did you mean: {', '.join(close)}?" if close else f" Known services: {', '.join(cmdb.names())}."
            raise ToolError(f"unknown service {service!r}.{hint}")
        if svc["status"] != "active":
            raise ToolError(f"service {service} is {svc['status']}; changes are not accepted")
        if window_start.tzinfo is None:
            raise ToolError("window_start needs a timezone, e.g. 2026-11-20T02:00:00Z")
        lead = window_start - store.now
        if lead <= dt.timedelta(0):
            raise ToolError("window_start is in the past")
        if lead > dt.timedelta(days=90):
            raise ToolError("window_start is more than 90 days ahead")
        if risk == "high" and lead < dt.timedelta(hours=48):
            raise ToolError("high-risk changes need a window at least 48 hours ahead")
        c = store.create(service, summary.strip(), risk, window_start.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), caller.user)
        return {"change_id": c["id"], "state": c["state"], "approver_group": svc["owner_group"]}

    @srv.tool(annotations=ToolAnnotations(read_only_hint=True))
    def get_change(change_id: ChangeId) -> dict:
        """Get one change: service, summary, risk, state, window, requester and comment count."""
        c = _load(change_id)
        return {**_summary(c), "requester": c["requester"], "comment_count": len(c["comments"])}

    @srv.tool(annotations=ToolAnnotations(read_only_hint=True))
    def list_my_open_changes(cursor: Annotated[str | None, Field(description="next_cursor from the previous page")] = None) -> dict:
        """List the signed-in user's open changes (draft, submitted, scheduled), 5 per page."""
        start = _offset(cursor)
        mine = [c for c in store.list_by_requester(caller.user) if c["state"] in OPEN_STATES]
        page = mine[start:start + PAGE_SIZE]
        nxt = start + PAGE_SIZE
        return {"changes": [_summary(c) for c in page], "next_cursor": _cursor(nxt) if nxt < len(mine) else None}

    @srv.tool()
    def add_comment(change_id: ChangeId, text: Annotated[str, Field(min_length=1, max_length=2000)]) -> dict:
        """Add a comment to a change. Only the requester or the service's owner group may comment."""
        c = _load(change_id)
        owner = (cmdb.lookup(c["service"]) or {}).get("owner_group")
        if caller.user != c["requester"] and owner not in caller.groups:
            raise ToolError(f"you may not comment on {change_id}: only the requester or {owner} can")
        return {"change_id": change_id, "comment_count": store.add_comment(change_id, caller.user, text.strip())}

    return srv
