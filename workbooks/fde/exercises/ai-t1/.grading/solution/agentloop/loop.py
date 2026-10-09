"""One customer turn against the Messages API: call the model, run the tools it asks for,
send the results back, repeat until it answers.

v2.14.0 (2026-10-08): tool calls in one round now run in parallel (p50 turn latency down
38%), and 429s are retried with jittered backoff instead of failing the turn.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from dataclasses import dataclass, field
from typing import Any, Protocol

import anthropic

from .tools import TOOLS

log = logging.getLogger("lumen.agent")

MODEL = "claude-sonnet-5"
MAX_TOKENS = 1024
MAX_ROUNDS = 8
TOOL_TIMEOUT_S = 2.0
RETRY_BASE_S = 0.5
MAX_RETRIES = 3

SYSTEM = (
    "You are Lumen Home's shopping assistant. Use the tools for every product, stock, "
    "delivery or order fact. When a tool is unavailable, say so and continue with what you have."
)


class ToolBox(Protocol):
    async def call(self, name: str, tool_input: dict[str, Any]) -> str: ...


@dataclass
class TurnResult:
    text: str
    rounds: int
    messages: list[dict[str, Any]] = field(default_factory=list)


def _event(name: str, level: int = logging.INFO, **fields: Any) -> None:
    log.log(level, json.dumps({"event": name, **fields}, sort_keys=True))


async def _create_with_retry(client: Any, *, turn_id: str, retry_base_s: float, **request: Any):
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await client.messages.create(**request)
        except anthropic.RateLimitError as exc:
            if attempt == MAX_RETRIES:
                raise
            hinted = float(exc.response.headers.get("retry-after") or 0)
            delay = max(hinted, retry_base_s * (2**attempt)) * random.uniform(0.5, 1.0)
            _event("rate_limited", logging.WARNING, turn_id=turn_id, attempt=attempt + 1, retry_in_ms=int(delay * 1000))
            await asyncio.sleep(delay)
    raise AssertionError("unreachable")


async def run_turn(
    client: Any,
    toolbox: ToolBox,
    messages: list[dict[str, Any]],
    *,
    turn_id: str = "t-0",
    tool_timeout_s: float = TOOL_TIMEOUT_S,
    retry_base_s: float = RETRY_BASE_S,
) -> TurnResult:
    """``messages`` is the conversation so far, ending with the customer's message; it is
    extended in place with this turn's assistant and tool_result messages."""
    for round_no in range(1, MAX_ROUNDS + 1):
        response = await _create_with_retry(
            client,
            turn_id=turn_id,
            retry_base_s=retry_base_s,
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM,
            tools=TOOLS,
            messages=messages,
        )
        messages.append(
            {"role": "assistant", "content": [b.model_dump(exclude_none=True) for b in response.content]}
        )
        _event("model_round", turn_id=turn_id, round=round_no, stop_reason=response.stop_reason)
        if response.stop_reason != "tool_use":
            text = "".join(b.text for b in response.content if b.type == "text")
            return TurnResult(text=text, rounds=round_no, messages=messages)

        calls = [b for b in response.content if b.type == "tool_use"]
        _event("tool_calls", turn_id=turn_id, round=round_no, tools=[c.name for c in calls])
        outcomes = await asyncio.gather(
            *(asyncio.wait_for(toolbox.call(c.name, dict(c.input)), tool_timeout_s) for c in calls),
            return_exceptions=True,
        )
        # Every tool_use gets exactly one tool_result, in tool_use order (gather keeps
        # it), as the first blocks of the next user message. A failure is an is_error
        # result the model can recover from, never a missing one.
        tool_results: list[dict[str, Any]] = []
        failed = 0
        for call, outcome in zip(calls, outcomes, strict=True):
            if isinstance(outcome, asyncio.CancelledError):
                raise outcome  # cancellation is not a tool failure
            if isinstance(outcome, BaseException):
                failed += 1
                _event(
                    "tool_failed", logging.WARNING, turn_id=turn_id, round=round_no,
                    tool=call.name, tool_use_id=call.id, error=type(outcome).__name__,
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "is_error": True,
                        # Class name only: the exception text can carry internal hosts.
                        "content": (
                            f"{call.name} is temporarily unavailable ({type(outcome).__name__}). "
                            "Continue with what you have and tell the customer what you could not check."
                        ),
                    }
                )
            else:
                tool_results.append({"type": "tool_result", "tool_use_id": call.id, "content": outcome})
        _event(
            "tools_done", turn_id=turn_id, round=round_no,
            calls=len(calls), results=len(tool_results), failed=failed,
        )
        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError(f"turn {turn_id} did not finish in {MAX_ROUNDS} rounds")
