"""Deterministic guardrails around the non-deterministic agent: ADK tool callbacks. See README task 1-2."""

from __future__ import annotations

import hashlib
import json  # noqa: F401
from datetime import datetime, timezone  # noqa: F401
from typing import Any, Callable

from . import systems

ALLOWED_TOOLS = (*systems.READ_TOOLS, "record_result")


def digest(obj: Any) -> str:
    """Stable SHA-256 of a tool result, for the execution log."""
    raise NotImplementedError("TODO: README task 2")


def make_before_tool(sample_ids: list[str], max_tool_calls: int = 16) -> Callable:
    """Return an ADK before_tool_callback(tool, args, tool_context) that returns None to let the
    call run, or {"error": <reason>, "blocked_by_guard": True} to block it without running it."""
    raise NotImplementedError("TODO: README task 1")


def make_after_tool(log: list[dict]) -> Callable:
    """Return an ADK after_tool_callback(tool, args, tool_context, tool_response) that appends one
    entry per tool call to `log`."""
    raise NotImplementedError("TODO: README task 2")
