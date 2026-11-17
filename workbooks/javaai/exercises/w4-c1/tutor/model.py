"""The model side of the tutor agent, in ADK terms.

In production this is an ADK ``LlmAgent`` on Gemini; here the model is any object with
``next_turn(history, tool_names) -> ModelTurn``. Tests script it. Do not change this file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FinalText:
    text: str


ModelTurn = ToolCall | FinalText


class TutorModel(Protocol):
    def next_turn(self, history: list[dict], tool_names: list[str]) -> ModelTurn: ...


class ScriptedModel:
    """Returns the scripted turns in order; repeats the last one when the script runs out."""

    def __init__(self, *turns: ModelTurn):
        self.turns = list(turns)
        self.calls: list[tuple[list[dict], list[str]]] = []

    def next_turn(self, history, tool_names):
        if len(self.calls) >= 25:
            raise RuntimeError("ScriptedModel: 25 model calls in one turn - the agent loop is unbounded")
        self.calls.append(([dict(m) for m in history], list(tool_names)))
        i = min(len(self.calls) - 1, len(self.turns) - 1)
        return self.turns[i]
