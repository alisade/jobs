"""Model clients. The loop talks to anything with create(system, messages, tools) -> response dict,
shaped like the Claude Messages API: {"stop_reason": "tool_use"|"end_turn",
"content": [{"type": "text", "text": ...}, {"type": "tool_use", "id": ..., "name": ..., "input": {...}}]}.

ScriptedModel replays recorded responses so everything runs offline. A live client is optional and
never used by tests or the grader."""

from __future__ import annotations

import copy
import json
from pathlib import Path


class ScriptedModel:
    def __init__(self, responses: list[dict]):
        self._responses = list(responses)
        self.calls: list[dict] = []   # what the loop sent on each call (deep copies)

    @classmethod
    def from_file(cls, path: str | Path) -> "ScriptedModel":
        return cls(json.loads(Path(path).read_text())["responses"])

    def create(self, system: str, messages: list[dict], tools: list[dict]) -> dict:
        self.calls.append({"system": system, "messages": copy.deepcopy(messages), "tools": copy.deepcopy(tools)})
        if not self._responses:
            return {"stop_reason": "end_turn", "content": [{"type": "text", "text": "(script exhausted)"}]}
        return self._responses.pop(0)
