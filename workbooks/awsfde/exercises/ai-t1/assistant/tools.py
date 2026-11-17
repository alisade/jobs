"""Tools for the report agent: two read tools and one write tool."""

from __future__ import annotations

import json
import logging
from typing import Any

from .context import JobContext

log = logging.getLogger("tidewater.tools")

TOOL_SPECS = [
    {"toolSpec": {"name": "search_docs", "description": "Search the tenant's documents.",
                  "inputSchema": {"json": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}},
    {"toolSpec": {"name": "get_weekly_metrics", "description": "Carrier metrics for last week.",
                  "inputSchema": {"json": {"type": "object", "properties": {"week": {"type": "string"}}}}}},
    {"toolSpec": {"name": "share_report", "description": "Email the finished report.",
                  "inputSchema": {"json": {"type": "object", "properties": {
                      "to": {"type": "array", "items": {"type": "string"}}, "subject": {"type": "string"},
                      "body": {"type": "string"}}, "required": ["to", "subject", "body"]}}}},
]
WRITE_TOOLS = {"share_report"}


class Tools:
    def __init__(self, kb: Any, metrics: dict, relay: Any, tenants: dict) -> None:
        self.kb, self.metrics, self.relay, self.tenants = kb, metrics, relay, tenants

    def search_docs(self, ctx: JobContext, args: dict) -> dict:
        docs = self.kb.search(ctx.tenant_id, args["query"])
        log.info(json.dumps({"event": "retrieval", "run_id": ctx.run_id, "doc_ids": [d["doc_id"] for d in docs]}))
        return {"text": "\n\n".join(d["text"] for d in docs)}

    def get_weekly_metrics(self, ctx: JobContext, args: dict) -> dict:
        return {"json": self.metrics[ctx.tenant_id]}

    def share_report(self, ctx: JobContext, args: dict) -> dict:
        msg_id = self.relay.send(ctx.tenant_id, args["to"], args["subject"], args["body"])
        return {"json": {"sent": True, "message_id": msg_id, "to": args["to"]}}

    def run(self, ctx: JobContext, name: str, args: dict) -> tuple[dict, str]:
        """Returns (content block, status)."""
        fn = getattr(self, name, None) if name in {s["toolSpec"]["name"] for s in TOOL_SPECS} else None
        if fn is None:
            return {"text": f"unknown tool {name}"}, "error"
        try:
            return fn(ctx, args), "success"
        except PermissionError as e:
            log.warning(json.dumps({"event": "tool_refused", "run_id": ctx.run_id, "tool": name, "reason": str(e)}))
            return {"text": f"refused: {e}"}, "error"
