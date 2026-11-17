"""Deterministic guardrails around the non-deterministic agent: ADK tool callbacks."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable

from . import systems

ALLOWED_TOOLS = (*systems.READ_TOOLS, "record_result")


def digest(obj: Any) -> str:
    """Stable SHA-256 of a tool result, for the execution log."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def _int(v: Any) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def make_before_tool(sample_ids: list[str], max_tool_calls: int = 16) -> Callable:
    sample = set(sample_ids)
    sample_prs = {systems.TICKETS[c]["pr_number"] for c in sample_ids if c in systems.TICKETS}

    def before_tool(tool, args: dict, tool_context) -> dict | None:
        used = int(tool_context.state.get("tool_calls", 0)) + 1
        tool_context.state["tool_calls"] = used
        reason = None
        if used > max_tool_calls:
            reason = f"tool budget exhausted ({max_tool_calls} calls per run); finish with the results you have"
        elif tool.name not in ALLOWED_TOOLS:
            reason = f"tool {tool.name} is not available to the CM-03 tester; allowed: {', '.join(ALLOWED_TOOLS)}"
        elif "change_id" in args and args["change_id"] not in sample:
            reason = f"{args['change_id']} is not in the current sample; call list_sample"
        elif "pr_number" in args and _int(args["pr_number"]) not in sample_prs:
            reason = f"PR {args['pr_number']} is not linked to a sampled change"
        elif tool.name == "record_result" and args.get("result") not in ("pass", "exception", "needs_review"):
            reason = "result must be pass, exception or needs_review"
        if reason:
            return {"error": reason, "blocked_by_guard": True}
        return None

    return before_tool


def make_after_tool(log: list[dict]) -> Callable:
    def after_tool(tool, args: dict, tool_context, tool_response) -> dict | None:
        blocked = isinstance(tool_response, dict) and tool_response.get("blocked_by_guard") is True
        entry = {
            "seq": len(log) + 1,
            "tool": tool.name,
            "args": dict(args),
            "blocked": blocked,
            "result_sha256": digest(tool_response),
            "at": datetime.now(timezone.utc).isoformat(),
        }
        if blocked:
            entry["reason"] = tool_response["error"]
        log.append(entry)
        return None

    return after_tool
