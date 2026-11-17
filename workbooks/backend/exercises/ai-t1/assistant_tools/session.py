"""The delegated identity of a tool call. keystone-mcp verifies the user's delegation token at
connection time (OAuth token exchange) and builds one Session per MCP session. Tool code never sees
the token, only this object."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Session:
    agent_id: str            # the agent app, e.g. "sales-assistant"
    user_id: str             # the human the agent acts on behalf of
    tenant_id: str           # the user's tenant, from the verified token
    trace_id: str
    scopes: frozenset = field(default_factory=lambda: frozenset({"crm.read"}))
