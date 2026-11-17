"""GRC MCP server for ControlPilot: read-only tools over one engagement, plus one gated write."""

from __future__ import annotations

import base64
import json
import time
from typing import Callable

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations

from .store import GrcStore
from .tokens import ApprovalError, verify_approval

READ = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)


def _cursor(offset: int, query: str, status: str | None) -> str:
    return base64.urlsafe_b64encode(json.dumps({"o": offset, "q": query, "s": status}).encode()).decode()


def _uncursor(cursor: str) -> dict:
    try:
        c = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        int(c["o"])
        return c
    except Exception:
        raise ToolError("invalid cursor: pass the next_cursor value from the previous search_exceptions result unchanged") from None


def build_server(store: GrcStore, *, engagement: str, approval_key: bytes, preparer: str,
                 now: Callable[[], float] = time.time) -> MCPServer:
    eng = store.engagement(engagement)  # KeyError for an unknown engagement: fail at startup, not per call
    server = MCPServer("mfh-grc", instructions=f"GRC data for engagement {engagement} only ({eng['name']}).")

    def control(control_id: str) -> dict:
        for c in eng["controls"]:
            if c["control_id"] == control_id:
                return c
        ids = ", ".join(c["control_id"] for c in eng["controls"])
        raise ToolError(f"control {control_id!r} not found in engagement {engagement}; valid ids: {ids} (see list_controls)")

    @server.tool(annotations=READ, description=(
        "List the controls in scope for this audit engagement: control_id, name, frequency and owner. "
        "Call this first to get valid control_id values for the other tools."))
    def list_controls() -> dict:
        return {"engagement": engagement, "controls": eng["controls"]}

    @server.tool(annotations=READ, description=(
        "Get the test record for one control in this engagement: procedure, population size, sample size, "
        "preparer, status and the sampled item ids. control_id comes from list_controls, e.g. 'CM-03'."))
    def get_control_test(control_id: str) -> dict:
        control(control_id)
        return eng["tests"][control_id]

    @server.tool(annotations=READ, description=(
        "Search recorded exceptions in this engagement. query matches the description or sample id "
        "(case-insensitive, empty matches all); status is 'open', 'closed' or omitted; limit 1-50. "
        "Results are sorted by exception_id; when next_cursor is not null, call again with the same "
        "query and status and cursor=next_cursor to get the next page."))
    def search_exceptions(query: str = "", status: str | None = None, cursor: str | None = None, limit: int = 10) -> dict:
        if status not in (None, "open", "closed"):
            raise ToolError(f"status must be 'open', 'closed' or omitted, not {status!r}")
        if not 1 <= limit <= 50:
            raise ToolError(f"limit must be between 1 and 50, got {limit}")
        offset = 0
        if cursor:
            c = _uncursor(cursor)
            if c.get("q") != query or c.get("s") != status:
                raise ToolError("cursor does not belong to this query: repeat the same query and status with the cursor, or start without one")
            offset = int(c["o"])
        q = query.casefold()
        hits = sorted((e for e in eng["exceptions"]
                       if (not q or q in e["description"].casefold() or q in e["sample_id"].casefold())
                       and (status is None or e["status"] == status)), key=lambda e: e["exception_id"])
        page = hits[offset:offset + limit]
        nxt = _cursor(offset + limit, query, status) if offset + limit < len(hits) else None
        return {"items": page, "total": len(hits), "next_cursor": nxt}

    @server.tool(annotations=READ, description=(
        "List the evidence documents filed for one sampled item of a control in this engagement "
        "(doc_id, title, page count). Returns an empty list when nothing is filed yet."))
    def get_evidence_index(control_id: str, sample_id: str) -> dict:
        control(control_id)
        if sample_id not in eng["tests"][control_id]["samples"]:
            raise ToolError(f"sample {sample_id!r} is not in the {control_id} sample; see get_control_test({control_id!r})")
        return {"control_id": control_id, "sample_id": sample_id,
                "documents": eng["evidence"].get(control_id, {}).get(sample_id, [])}

    @server.tool(annotations=WRITE, description=(
        "Record a confirmed control exception in the GRC system. Requires approval_token, issued by a "
        "human reviewer (not the preparer) for exactly this engagement, control_id and sample_id; you "
        "cannot create one yourself. Without a valid token the call is rejected; ask for review instead. "
        "description: what failed, at least 20 characters."))
    def record_exception(control_id: str, sample_id: str, description: str, approval_token: str) -> dict:
        control(control_id)
        if sample_id not in eng["tests"][control_id]["samples"]:
            raise ToolError(f"sample {sample_id!r} is not in the {control_id} sample")
        if len(description.strip()) < 20:
            raise ToolError("description must say what failed (at least 20 characters)")
        try:
            a = verify_approval(approval_key, approval_token, engagement=engagement,
                                control_id=control_id, sample_id=sample_id, now=now())
        except ApprovalError as e:
            raise ToolError(f"not authorized: {e}") from None
        if a.reviewer.strip().casefold() == preparer.strip().casefold():
            raise ToolError("not authorized: the reviewer on the approval is the preparer; a different reviewer must approve")
        for e in eng["exceptions"]:
            if e["control_id"] == control_id and e["sample_id"] == sample_id and e["status"] == "open":
                raise ToolError(f"an open exception is already recorded for {control_id}/{sample_id}: {e['exception_id']}")
        rec = store.add_exception(engagement, {"control_id": control_id, "sample_id": sample_id,
                                              "description": description.strip(), "status": "open",
                                              "raised_by": preparer, "approved_by": a.reviewer})
        return {"exception_id": rec["exception_id"], "status": "open", "approved_by": a.reviewer}

    return server
