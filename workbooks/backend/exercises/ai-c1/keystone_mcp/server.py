"""keystone-mcp: task-level tools for agents over Keystone.

A first prototype from the sales-assistant hackathon. It works in the demo, which had one tenant.
Make it production-ready per README.md: scoped to the delegated user's tenant, scope checks,
idempotent writes, proposals instead of direct writes, and an audit entry for every call.
"""

from __future__ import annotations

import time
from typing import Callable

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from .audit import AuditLog, args_digest  # noqa: F401
from .identity import verify_delegation
from .store import Store
from .workflows import FakeWorkflowClient


def build_server(token: str, *, store: Store, audit: AuditLog, workflows: FakeWorkflowClient, secret: bytes,
                 clock: Callable[[], float] = time.time) -> MCPServer:
    ident = verify_delegation(token, secret, clock())
    server = MCPServer(name="keystone-mcp")

    @server.tool(description="find accounts")
    def find_account(query: str, limit: int = 10) -> dict:
        hits = store.search_accounts(None, query)[:limit]
        return {"accounts": [{"id": a.id, "name": a.name, "owner_id": a.owner_id} for a in hits]}

    @server.tool(description="timeline")
    def get_account_timeline(account_id: str, limit: int = 20) -> dict:
        items = [{"id": x.id, "type": x.type, "subject": x.subject, "body": x.body, "occurred_at": x.occurred_at}
                 for x in store.timeline(account_id, limit)]
        return {"account_id": account_id, "items": items}

    @server.tool(description="log an activity")
    def log_activity(account_id: str, type: str, subject: str, idempotency_key: str) -> dict:  # noqa: A002
        # TODO: scopes, validation, tenant check, idempotency, audit
        a = store.add_activity(ident.tenant, account_id, type, subject, ident.user_id, "2026-11-16T00:00:00Z")
        return {"activity_id": a.id, "account_id": account_id, "replayed": False}

    @server.tool(description="assign a lead")
    def propose_lead_assignment(lead_id: str, owner_id: str, reason: str = "") -> dict:
        # TODO: this must start an approval, not assign
        if store.get_lead(lead_id) is None:
            raise ToolError("lead not found")
        store.assign_lead(lead_id, owner_id)
        return {"status": "assigned"}

    return server
