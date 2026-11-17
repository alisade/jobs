"""The agent loop. TODO: implement run_turn (see README, "Loop contract")."""
from __future__ import annotations

import json  # noqa: F401
from dataclasses import dataclass, field

from parts_agent.session import SYSTEM_PROMPT, Session  # noqa: F401
from parts_agent.tools import TOOLS, execute_tool  # noqa: F401

TURN_LIMIT_TEXT = "I could not finish this request within the step limit. Please try again or call the parts desk."


@dataclass
class RunResult:
    final_text: str
    stop_reason: str                      # end_turn | max_tokens | max_turns
    model_calls: int
    tool_calls: list[dict] = field(default_factory=list)   # {"name", "input", "is_error"}
    usage: dict = field(default_factory=lambda: {"input_tokens": 0, "output_tokens": 0})


def run_turn(client, session: Session, user_text: str, *, max_turns: int = 8,
             model: str = "fake-model", max_tokens: int = 1024) -> RunResult:
    # TODO
    raise NotImplementedError
