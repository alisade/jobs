"""Tools exposed to the sales assistant. Schemas are what the model sees."""

from __future__ import annotations

from . import audit
from .data import ACCOUNTS, ACTIVITIES
from .session import Session

TOOLS = {
    "find_account": {
        "description": "Find accounts by name. Returns id, name and owner for up to 10 matches.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "part of the account name"}},
            "required": ["query"],
        },
    },
    "get_account_timeline": {
        "description": ("Get the newest activities (calls, emails, meetings) for an account. Use tenant_id to "
                        "look at accounts in another business unit when the user needs cross-BU context."),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "tenant_id": {"type": "string", "description": "business unit; defaults to the user's own"},
                "limit": {"type": "integer", "description": "max items"},
            },
            "required": ["account_id"],
        },
    },
}


class ToolError(Exception):
    pass


def find_account(session: Session, args: dict) -> dict:
    q = str(args["query"]).lower()
    hits = [a for a in ACCOUNTS if a["tenant_id"] == session.tenant_id and q in a["name"].lower()][:10]
    return {"accounts": [{"id": a["id"], "name": a["name"], "owner": a["owner"]} for a in hits]}


def get_account_timeline(session: Session, args: dict) -> dict:
    tenant = args.get("tenant_id") or session.tenant_id
    acct = next((a for a in ACCOUNTS if a["id"] == args["account_id"] and a["tenant_id"] == tenant), None)
    if acct is None:
        raise ToolError("account not found")
    items = [x for x in ACTIVITIES if x["account_id"] == acct["id"]]
    items.sort(key=lambda x: x["at"], reverse=True)
    if args.get("limit"):
        items = items[: int(args["limit"])]
    return {"account": {"id": acct["id"], "name": acct["name"]},
            "activities": [{"id": x["id"], "kind": x["kind"], "at": x["at"], "note": x["note"]} for x in items]}


HANDLERS = {"find_account": find_account, "get_account_timeline": get_account_timeline}


def call_tool(session: Session, name: str, args: dict) -> dict:
    """Entry point used by the MCP server for tools/call. Returns an MCP-style result."""
    if name not in HANDLERS:
        return {"is_error": True, "content": f"unknown tool {name}"}
    try:
        out = HANDLERS[name](session, args)
    except ToolError as exc:
        return {"is_error": True, "content": str(exc)}
    audit.record({"actor": session.agent_id, "tool": name, "outcome": "ok"})
    return {"is_error": False, "content": out}
