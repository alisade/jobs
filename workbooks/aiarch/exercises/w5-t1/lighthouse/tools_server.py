"""Change-management tool server (runs behind AgentCore Gateway in prod). Works as shipped: it
continues the caller's trace from the W3C traceparent header it receives."""
from __future__ import annotations

import time

from opentelemetry import propagate, trace
from opentelemetry.trace import SpanKind

tracer = trace.get_tracer("lighthouse.tools")

CHANGES = {"CHG-9001": {"state": "scheduled"}, "CHG-9002": {"state": "open"}, "CHG-9003": {"state": "closed"}}


def handle(name: str, args: dict, headers: dict) -> dict:
    ctx = propagate.extract(headers)
    with tracer.start_as_current_span(f"tools/call {name}", context=ctx, kind=SpanKind.SERVER,
                                      attributes={"mcp.method.name": "tools/call", "gen_ai.tool.name": name}) as span:
        time.sleep(0.01)
        if name == "get_change":
            item = CHANGES.get(args.get("change_id", ""))
            span.set_attribute("lighthouse.found", item is not None)
            return {"change_id": args.get("change_id"), **(item or {"error": "not found"})}
        return {"error": f"unknown tool {name}"}
