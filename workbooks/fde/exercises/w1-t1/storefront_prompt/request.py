"""The Messages API request every worker sends: tools, system, messages, three breakpoints."""

from __future__ import annotations

from typing import Any

from .prompt import build_static_system
from .tools import build_tools

EPHEMERAL = {"type": "ephemeral"}
MODEL = "claude-sonnet-5"


def build_request(
    flags: dict[str, Any], dynamic_context: str, messages: list[dict[str, Any]]
) -> dict[str, Any]:
    tools = build_tools(flags)
    if tools:
        tools[-1]["cache_control"] = dict(EPHEMERAL)
    request_messages = [dict(m) for m in messages]
    if request_messages:
        # Rolling breakpoint on the newest message, so earlier rounds read from cache.
        last = request_messages[-1]
        content = last["content"]
        blocks = [{"type": "text", "text": content}] if isinstance(content, str) else [dict(b) for b in content]
        blocks[-1]["cache_control"] = dict(EPHEMERAL)
        request_messages[-1] = {**last, "content": blocks}
    return {
        "model": MODEL,
        "max_tokens": 1024,
        "tools": tools,
        "system": [
            {"type": "text", "text": build_static_system(flags), "cache_control": dict(EPHEMERAL)},
            {"type": "text", "text": dynamic_context},
        ],
        "messages": request_messages,
    }
