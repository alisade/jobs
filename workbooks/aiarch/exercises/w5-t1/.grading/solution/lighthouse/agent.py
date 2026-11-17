"""One agent turn: a model call that may request several tools; tool calls run in parallel.

Spans follow the OTEL GenAI conventions: invoke_agent (root), chat (model call), execute_tool
(one per tool call, CLIENT). The tool call carries traceparent to the tool server.
"""
from __future__ import annotations

import contextvars
from concurrent.futures import ThreadPoolExecutor

from opentelemetry import propagate, trace
from opentelemetry.trace import SpanKind

from . import tools_server

tracer = trace.get_tracer("lighthouse.agent")
POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="tool")


def _call_tool(call: dict) -> dict:
    with tracer.start_as_current_span(f"execute_tool {call['name']}", kind=SpanKind.CLIENT,
                                      attributes={"gen_ai.operation.name": "execute_tool",
                                                  "gen_ai.tool.name": call["name"],
                                                  "gen_ai.tool.call.id": call["id"]}):
        headers: dict = {}
        propagate.inject(headers)
        return tools_server.handle(call["name"], call["args"], headers)


def run_turn(session_id: str, tool_calls: list[dict]) -> list[dict]:
    """tool_calls: what the (stubbed) model asked for in this turn."""
    with tracer.start_as_current_span("invoke_agent change_assistant",
                                      attributes={"gen_ai.operation.name": "invoke_agent",
                                                  "gen_ai.agent.name": "change_assistant",
                                                  "session.id": session_id}):
        with tracer.start_as_current_span("chat us.anthropic.claude-haiku-4-5-20251001-v1:0",
                                          attributes={"gen_ai.operation.name": "chat",
                                                      "gen_ai.usage.input_tokens": 1800,
                                                      "gen_ai.usage.output_tokens": 120}):
            pass
        if len(tool_calls) == 1:
            return [_call_tool(tool_calls[0])]
        # Worker threads do not inherit contextvars, so the active span (the OTEL context) would be
        # lost and every execute_tool span would start a new trace. Run each call in its own copy
        # of the caller's context (one copy per task: a Context cannot be entered twice at once).
        futures = [POOL.submit(contextvars.copy_context().run, _call_tool, c) for c in tool_calls]
        return [f.result(timeout=30) for f in futures]
