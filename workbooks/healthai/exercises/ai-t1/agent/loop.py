"""Agent loop over a scripted model: each model turn is a list of tool calls or a final text."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .prompts import SYSTEM_PROMPT
from .tools import Tools


class ScriptedModel:
    """Replays recorded turns. A real model would see `messages`; this one ignores them."""

    def __init__(self, turns: list[dict[str, Any]]):
        self.turns = list(turns)

    @classmethod
    def from_file(cls, path: str | Path) -> "ScriptedModel":
        return cls(json.loads(Path(path).read_text())["turns"])

    def next(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        return self.turns.pop(0) if self.turns else {"text": "done"}


def run_agent(model: ScriptedModel, tools: Tools, case_id: str, max_turns: int = 8) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT},
                                      {"role": "user", "content": f"Draft a determination for {case_id}."}]
    for _ in range(max_turns):
        turn = model.next(messages)
        if "text" in turn:
            messages.append({"role": "assistant", "content": turn["text"]})
            break
        messages.append({"role": "assistant", "tool_calls": turn["tool_calls"]})
        for call in turn["tool_calls"]:
            result = tools.call(call["name"], call["args"])
            messages.append({"role": "tool", "name": call["name"], "content": result})
    return messages
