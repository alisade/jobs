"""Test helpers: build a session for a synthetic user and call tools through a real MCP client."""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from mcp import Client

from keystone_mcp.audit import AuditLog
from keystone_mcp.identity import sign_delegation
from keystone_mcp.server import build_server
from keystone_mcp.store import Store, demo_store
from keystone_mcp.workflows import FakeWorkflowClient

SECRET = b"keystone-test-secret"
NOW = 1_794_830_400.0  # 2026-11-16T12:00:00Z


@dataclass
class World:
    store: Store = field(default_factory=demo_store)
    audit: AuditLog = field(default_factory=AuditLog)
    workflows: FakeWorkflowClient = field(default_factory=FakeWorkflowClient)


def token(user="usr-amer-rep-1", tenant="bu-amer", scopes=("crm.read", "crm.write"), agent="sales-assistant",
          exp=NOW + 3600, secret=SECRET) -> str:
    return sign_delegation({"sub": user, "tenant": tenant, "scopes": list(scopes), "agent": agent, "exp": exp}, secret)


@asynccontextmanager
async def session(world: World, tok: str):
    server = build_server(tok, store=world.store, audit=world.audit, workflows=world.workflows,
                          secret=SECRET, clock=lambda: NOW)
    async with Client(server) as c:
        yield c


async def call(client, tool: str, args: dict) -> tuple[bool, object]:
    r = await client.call_tool(tool, args)
    text = "".join(getattr(x, "text", "") for x in r.content)
    if r.is_error:
        return True, text
    return False, json.loads(text)
