"""Recorded-replay stand-in for ``anthropic.AsyncAnthropic``. Given; do not change.

``FakeAnthropic(script).messages.create(...)`` returns the next recorded model response as
a real ``anthropic.types.Message``, after validating the request the way the Messages API
does. A request the real API would reject raises the SDK's own ``anthropic.BadRequestError``
(HTTP 400, ``invalid_request_error``) with the API's wording. ``rate_limit_calls`` makes
chosen calls (0-based, counting every attempt) answer HTTP 429 first, as production does
under load.

No network, no API key: nothing here talks to Anthropic.
"""

from __future__ import annotations

import copy
import itertools
from typing import Any

import anthropic
import httpx
from anthropic.types import Message

_URL = "https://api.anthropic.com/v1/messages"
_ids = itertools.count(1)


def _error(status: int, kind: str, message: str, headers: dict[str, str] | None = None):
    body = {"type": "error", "error": {"type": kind, "message": message}}
    response = httpx.Response(
        status, request=httpx.Request("POST", _URL), json=body, headers=headers or {}
    )
    cls = anthropic.BadRequestError if status == 400 else anthropic.RateLimitError
    return cls(f"Error code: {status} - {body}", response=response, body=body)


def validate_request(messages: list[dict[str, Any]]) -> str | None:
    """The API's message-shape checks this loop can trip. Returns the error text or None."""
    if not messages or messages[0].get("role") != "user":
        return "messages: first message must use the \"user\" role"
    for i, msg in enumerate(messages):
        role = msg.get("role")
        if i and role == messages[i - 1].get("role"):
            return f"messages.{i}: roles must alternate between \"user\" and \"assistant\""
        content = msg.get("content")
        if isinstance(content, list) and not content:
            return f"messages.{i}: all messages must have non-empty content except for the optional final assistant message"
        if role != "user" or not isinstance(content, list):
            continue
        prev = messages[i - 1] if i else {"content": []}
        prev_blocks = prev.get("content") if isinstance(prev.get("content"), list) else []
        uses = [b["id"] for b in prev_blocks if isinstance(b, dict) and b.get("type") == "tool_use"]
        for j, block in enumerate(content):
            if isinstance(block, dict) and block.get("type") == "tool_result":
                if block.get("tool_use_id") not in uses:
                    return (
                        f"messages.{i}.content.{j}: unexpected `tool_use_id` found in "
                        f"`tool_result` blocks: {block.get('tool_use_id')}. Each `tool_result` "
                        "block must have a corresponding `tool_use` block in the previous message."
                    )
    for i, msg in enumerate(messages):
        if msg.get("role") != "assistant" or not isinstance(msg.get("content"), list):
            continue
        uses = [b["id"] for b in msg["content"] if isinstance(b, dict) and b.get("type") == "tool_use"]
        if not uses:
            continue
        nxt = messages[i + 1] if i + 1 < len(messages) else None
        leading: list[str] = []
        if nxt is not None and isinstance(nxt.get("content"), list):
            for block in nxt["content"]:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    leading.append(block.get("tool_use_id"))
                else:
                    break  # tool_result blocks must come first in the user message
        missing = [u for u in uses if u not in leading]
        if nxt is not None and missing:
            return (
                f"messages.{i + 1}: `tool_use` ids were found without `tool_result` blocks "
                f"immediately after: {', '.join(missing)}. Each `tool_use` block must have a "
                "corresponding `tool_result` block in the next message."
            )
    return None


class FakeMessages:
    def __init__(self, script: list[dict[str, Any]], rate_limit_calls: set[int] | None = None):
        self._script = list(script)
        self._rate_limit_calls = set(rate_limit_calls or ())
        self.attempts = 0
        self.requests: list[dict[str, Any]] = []  # deep copies, as sent

    async def create(self, *, model: str, max_tokens: int, messages: list[dict[str, Any]], **kw: Any) -> Message:
        attempt = self.attempts
        self.attempts += 1
        request = copy.deepcopy({"model": model, "max_tokens": max_tokens, "messages": messages, **kw})
        self.requests.append(request)
        if attempt in self._rate_limit_calls:
            raise _error(
                429,
                "rate_limit_error",
                "This request would exceed the rate limit for your organization. Please retry later.",
                {"retry-after": "0"},
            )
        problem = validate_request(request["messages"])
        if problem is not None:
            raise _error(400, "invalid_request_error", problem)
        if not self._script:
            raise _error(400, "invalid_request_error", "replay: no recorded response left for this request")
        step = self._script.pop(0)
        return Message.model_validate(
            {
                "id": f"msg_{next(_ids):06d}",
                "type": "message",
                "role": "assistant",
                "model": model,
                "content": step["content"],
                "stop_reason": step["stop_reason"],
                "stop_sequence": None,
                "usage": {"input_tokens": 900, "output_tokens": 60},
            }
        )


class FakeAnthropic:
    def __init__(self, script: list[dict[str, Any]], rate_limit_calls: set[int] | None = None):
        self.messages = FakeMessages(script, rate_limit_calls)
