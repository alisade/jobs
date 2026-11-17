"""A fake AsyncAnthropic for offline work. Given; do not change.

``FakeAnthropic(script)`` replays recorded responses (``fixtures/*.json``) one per
``client.messages.create(...)`` call and returns real ``anthropic.types.Message`` objects.
Before answering, it validates the request the way the Messages API does and raises
``FakeBadRequest`` (status 400) with the API's wording when a request would be rejected:

- the conversation starts with a user message and roles alternate
- every tool_use in an assistant message is answered by a tool_result with the same id in
  the very next user message, and the tool_result blocks come first in that message
- no tool_result answers an id the previous assistant message did not issue
- at most 4 blocks carry ``cache_control``
- ``tool_choice`` and tool_use/tool_result history require ``tools`` in the request

Every accepted request is deep-copied into ``client.requests`` for assertions.
"""

from __future__ import annotations

import copy
import itertools
import json
from pathlib import Path
from typing import Any

from anthropic.types import Message

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
_ids = itertools.count(1)


class FakeBadRequest(Exception):
    """What anthropic.BadRequestError carries: a 400 with an invalid_request_error."""

    status_code = 400

    def __init__(self, message: str) -> None:
        super().__init__(f"Error code: 400 - invalid_request_error: {message}")
        self.message = message


def load_script(name: str) -> list[dict[str, Any]]:
    """A recorded conversation: one response dict per model call."""
    return json.loads((FIXTURES / f"{name}.json").read_text())["responses"]


def _plain(block: Any) -> dict[str, Any]:
    if hasattr(block, "model_dump"):
        return block.model_dump(exclude_none=True)
    return block


def _blocks(content: Any) -> list[dict[str, Any]]:
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [_plain(b) for b in content]


def _count_cache_control(request: dict[str, Any]) -> int:
    count = 0
    system = request.get("system")
    if isinstance(system, list):
        count += sum(1 for b in system if _plain(b).get("cache_control"))
    count += sum(1 for t in request.get("tools") or [] if t.get("cache_control"))
    for message in request.get("messages", []):
        if not isinstance(message.get("content"), str):
            count += sum(1 for b in _blocks(message["content"]) if b.get("cache_control"))
    return count


def validate_request(request: dict[str, Any]) -> None:
    for key in ("model", "max_tokens", "messages"):
        if key not in request:
            raise FakeBadRequest(f"{key}: Field required")
    messages = request["messages"]
    if not messages or messages[0].get("role") != "user":
        raise FakeBadRequest("messages: the first message must use the \"user\" role")
    tools = request.get("tools") or []
    if request.get("tool_choice") is not None and not tools:
        raise FakeBadRequest("tool_choice may only be specified while providing tools.")
    previous_tool_ids: list[str] = []
    saw_tool_blocks = False
    for index, message in enumerate(messages):
        role = message.get("role")
        if index and role == messages[index - 1].get("role"):
            raise FakeBadRequest(f"messages.{index}: roles must alternate between \"user\" and \"assistant\"")
        blocks = _blocks(message.get("content", ""))
        if role == "assistant":
            previous_tool_ids = [b["id"] for b in blocks if b.get("type") == "tool_use"]
            saw_tool_blocks = saw_tool_blocks or bool(previous_tool_ids)
            continue
        results = [b for b in blocks if b.get("type") == "tool_result"]
        saw_tool_blocks = saw_tool_blocks or bool(results)
        leading = list(itertools.takewhile(lambda b: b.get("type") == "tool_result", blocks))
        if len(leading) != len(results):
            raise FakeBadRequest(
                f"messages.{index}: tool_result blocks must come first in the user message, "
                "before any other content"
            )
        answered = [b.get("tool_use_id") for b in results]
        missing = [i for i in previous_tool_ids if i not in answered]
        if missing:
            raise FakeBadRequest(
                f"messages.{index - 1}: `tool_use` ids were found without `tool_result` blocks "
                f"immediately after: {', '.join(missing)}. Each `tool_use` block must have a "
                "corresponding `tool_result` block in the next message."
            )
        unexpected = [i for i in answered if i not in previous_tool_ids]
        if unexpected:
            raise FakeBadRequest(
                f"messages.{index}.content: unexpected `tool_use_id` found in `tool_result` "
                f"blocks: {', '.join(unexpected)}. Each `tool_result` block must have a "
                "corresponding `tool_use` block in the previous message."
            )
        for b in results:
            if "is_error" in b and not isinstance(b["is_error"], bool):
                raise FakeBadRequest(f"messages.{index}: tool_result.is_error must be a boolean")
        previous_tool_ids = []
    if messages[-1].get("role") == "assistant" and previous_tool_ids:
        raise FakeBadRequest("the final assistant message has unanswered tool_use blocks")
    if saw_tool_blocks and not tools:
        raise FakeBadRequest(
            "Requests which include `tool_use` or `tool_result` blocks must define tools."
        )
    if _count_cache_control(request) > 4:
        raise FakeBadRequest("A maximum of 4 blocks with cache_control may be provided. Found more.")


class _Messages:
    def __init__(self, client: FakeAnthropic) -> None:
        self._client = client

    async def create(self, **request: Any) -> Message:
        validate_request(request)
        self._client.requests.append(copy.deepcopy(request))
        if not self._client.script:
            raise AssertionError("fake client: the recorded script has no response left")
        recorded = self._client.script.pop(0)
        tool_names = {t["name"] for t in request.get("tools") or []}
        uses = [b for b in recorded["content"] if b["type"] == "tool_use"]
        choice = (request.get("tool_choice") or {}).get("type")
        if uses and choice == "none":
            raise AssertionError("fake client: script has tool_use where tool_choice is none")
        for b in uses:
            if b["name"] not in tool_names:
                raise FakeBadRequest(f"tool {b['name']!r} is not defined in tools")
        usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0,
                 "cache_creation_input_tokens": 0}
        usage.update(recorded.get("usage", {}))
        return Message.model_validate(
            {
                "id": f"msg_fake_{next(_ids):04d}",
                "type": "message",
                "role": "assistant",
                "model": request["model"],
                "content": recorded["content"],
                "stop_reason": recorded["stop_reason"],
                "stop_sequence": None,
                "usage": usage,
            }
        )


class FakeAnthropic:
    """Shaped like ``anthropic.AsyncAnthropic`` for ``client.messages.create``."""

    def __init__(self, script: list[dict[str, Any]]) -> None:
        self.script = list(script)
        self.requests: list[dict[str, Any]] = []
        self.messages = _Messages(self)
