"""The tutor agent loop (the part ADK's Runner does for you, written out so you own the guardrails).

TODO(w4-c1): see README "Requirements". The prototype below trusts the model completely.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import tools
from .model import FinalText, ToolCall, TutorModel


@dataclass
class TurnResult:
    reply: str
    tool_calls: list[str] = field(default_factory=list)
    refused: bool = False      # the before-model guard refused (off topic)
    withheld: bool = False     # the after-model guard replaced a reply that gave the answer away


class TutorAgent:
    def __init__(self, model: TutorModel):
        self.model = model

    def run_turn(self, learner_id: str, course_id: str, message: str) -> TurnResult:
        history = [{"role": "user", "text": message}]
        names = list(tools.REGISTRY)
        called: list[str] = []
        while True:
            turn = self.model.next_turn(history, names)
            if isinstance(turn, FinalText):
                return TurnResult(reply=turn.text, tool_calls=called)
            assert isinstance(turn, ToolCall)
            result = tools.REGISTRY[turn.name](**turn.args)
            called.append(turn.name)
            history.append({"role": "tool", "name": turn.name, "result": result})
