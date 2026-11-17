"""A Messages API agent loop over the blueprint's tool executor. Reference solution."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Protocol

from commerce_common.streaming import AgentEvent, ToolOutcome

USAGE_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_read_input_tokens",
    "cache_creation_input_tokens",
)
EPHEMERAL = {"type": "ephemeral"}


class ToolExecutor(Protocol):
    async def execute(self, name: str, tool_input: dict[str, Any] | None) -> ToolOutcome: ...


@dataclass
class TurnResult:
    final_text: str
    stop_reason: str
    rounds: int  # model calls made this turn
    messages: list[dict[str, Any]]  # the conversation after the turn
    usage: dict[str, int] = field(default_factory=lambda: dict.fromkeys(USAGE_FIELDS, 0))
    events: list[AgentEvent] = field(default_factory=list)  # host events, in tool_use order


def build_request(
    *,
    model: str,
    static_system: str,
    dynamic_context: str,
    tools: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    max_tokens: int = 1024,
    tool_choice: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Static system text carries a breakpoint; the per-request context is a second block
    after it; the last tool carries the other breakpoint. The caller's tools are copied."""
    request_tools = [dict(t) for t in tools]
    if request_tools:
        request_tools[-1]["cache_control"] = dict(EPHEMERAL)
    request: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": [
            {"type": "text", "text": static_system, "cache_control": dict(EPHEMERAL)},
            {"type": "text", "text": dynamic_context},
        ],
        "tools": request_tools,
        "messages": list(messages),
    }
    if tool_choice is not None:
        request["tool_choice"] = tool_choice
    return request


def _add_usage(total: dict[str, int], usage: Any) -> None:
    for name in USAGE_FIELDS:
        total[name] += int(getattr(usage, name, 0) or 0)


async def run_turn(
    client: Any,
    executor: ToolExecutor,
    *,
    model: str,
    static_system: str,
    dynamic_context: str,
    tools: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    user_text: str,
    max_iterations: int = 6,
    max_tokens: int = 1024,
) -> TurnResult:
    conversation = [*messages, {"role": "user", "content": user_text}]
    result = TurnResult(final_text="", stop_reason="", rounds=0, messages=conversation)
    tool_rounds = 0
    while True:
        forced = tool_rounds >= max_iterations
        request = build_request(
            model=model,
            static_system=static_system,
            dynamic_context=dynamic_context,
            tools=tools,
            messages=conversation,
            max_tokens=max_tokens,
            tool_choice={"type": "none"} if forced else None,
        )
        response = await client.messages.create(**request)
        result.rounds += 1
        _add_usage(result.usage, response.usage)
        content = [block.model_dump(exclude_none=True) for block in response.content]
        conversation.append({"role": "assistant", "content": content})
        result.stop_reason = response.stop_reason or ""
        uses = [b for b in response.content if b.type == "tool_use"]
        if response.stop_reason != "tool_use" or not uses or forced:
            result.final_text = "".join(b.text for b in response.content if b.type == "text")
            return result
        outcomes = await asyncio.gather(*(executor.execute(u.name, dict(u.input)) for u in uses))
        tool_results = []
        for use, outcome in zip(uses, outcomes, strict=True):
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": use.id,
                    "content": outcome.result_text,
                    "is_error": outcome.is_error,
                }
            )
            result.events.extend(outcome.events)
        conversation.append({"role": "user", "content": tool_results})
        tool_rounds += 1
