"""Model stand-ins. Do not change.

FollowsInstructionsModel reproduces what the incident shows: a model that reads a lesson and obeys
instructions it finds in tool results when the requested tool is available to it. Real models
resist this most of the time, which is exactly why it cannot be the control.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Final:
    text: str


class FollowsInstructionsModel:
    def __init__(self):
        self.offered: list[list[str]] = []

    def next_turn(self, system: str, history: list[dict], tools: list[str]):
        self.offered.append(list(tools))
        results = [h for h in history if h["role"] == "tool"]
        pending = [h for h in history if h["role"] == "pending"]
        if pending:
            return pending[0]["call"]
        if not results and "get_lesson" in tools:
            m = re.search(r"\b(l\d+)\b", history[0]["text"])
            return ToolCall("get_lesson", {"lesson_id": m.group(1) if m else "l6"})
        seen_text = " ".join(str(h["result"]) for h in results)
        wanted = re.findall(r"call (\w+) for ((?:lesson \w+(?: and )?)+)", seen_text)
        done = {(h["name"], str(h.get("args"))) for h in results}
        for tool, lessons in wanted:
            if tool in tools:
                for lid in re.findall(r"lesson (\w+)", lessons):
                    args = {"learner_id": "<session>", "lesson_id": lid}
                    if (tool, str(args)) not in done:
                        return ToolCall(tool, args)
        return Final("Antifungal drugs usually target ergosterol in the fungal membrane. Which structure do antibiotics target instead?")


class ScriptedModel:
    def __init__(self, *turns):
        self.turns = list(turns)
        self.offered: list[list[str]] = []

    def next_turn(self, system, history, tools):
        self.offered.append(list(tools))
        return self.turns[min(len(self.offered) - 1, len(self.turns) - 1)]
