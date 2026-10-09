"""A Messages API agent loop over the blueprint's tool executor.

YOUR WORK GOES HERE. Read README.md for the acceptance criteria. The executor is the
blueprint's ShoppingToolExecutor (or anything with the same ``execute``); the client is
anything shaped like ``anthropic.AsyncAnthropic`` (the tests use agent_loop.fake_client).
"""

from __future__ import annotations

import asyncio  # noqa: F401  (you will need it)
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
    """The kwargs for client.messages.create.

    TODO: lay the request out like commerce_common.prompt_assembly:
      - system: the static text as the first block, carrying cache_control ephemeral;
        the dynamic (per-request) context as a second block with no cache_control
      - tools: a copy of ``tools`` with cache_control on the LAST tool only; the caller's
        list and dicts must not be modified
      - tool_choice only when given
    """
    raise NotImplementedError("build_request")


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
    """Run one customer turn to completion.

    TODO:
      - append the user message to a copy of ``messages`` (do not mutate the caller's list)
      - call the model; persist the assistant message; sum usage (all four fields)
      - on stop_reason "tool_use": run every tool_use block concurrently through
        ``executor.execute``, answer each with a tool_result in tool_use order in one user
        message, is_error taken from the outcome (a held outcome is NOT an error), collect
        outcome.events
      - any other stop_reason ends the turn; final_text is the response's text blocks
      - after ``max_iterations`` tool rounds, make one last call with tool_choice none
        (keep the tools in the request: dropping them changes the cached prefix)
    """
    raise NotImplementedError("run_turn")
