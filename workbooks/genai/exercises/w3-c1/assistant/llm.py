"""Model client interface and a scripted fake (complete; do not change the interface).

The shapes follow the Messages API: an assistant response is a list of content blocks, either
{"type": "text", "text": ...} or {"type": "tool_use", "id": ..., "name": ..., "input": {...}}.
Tool results go back in a user message as
{"type": "tool_result", "tool_use_id": ..., "content": "<string>", "is_error": bool}.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

Block = dict[str, Any]
Message = dict[str, Any]


@dataclass
class LLMResponse:
    content: list[Block]
    stop_reason: str = "end_turn"  # "end_turn" | "tool_use"


class LLMClient(Protocol):
    def complete(self, system: str, messages: list[Message], tools: list[dict]) -> LLMResponse: ...


def text(t: str) -> LLMResponse:
    return LLMResponse([{"type": "text", "text": t}], "end_turn")


def tool_use(name: str, input: dict, id: str = "tu_1", preface: str | None = None) -> LLMResponse:
    blocks: list[Block] = []
    if preface:
        blocks.append({"type": "text", "text": preface})
    blocks.append({"type": "tool_use", "id": id, "name": name, "input": input})
    return LLMResponse(blocks, "tool_use")


Step = LLMResponse | Callable[[list[Message]], LLMResponse]


@dataclass
class ScriptedLLM:
    """Returns the scripted steps in order. A step may be a function of the messages so far.

    Records every call (deep copies) in .calls for assertions. When the script runs out it keeps
    returning the last step, which lets tests model a model that loops forever.
    """

    steps: list[Step]
    calls: list[dict] = field(default_factory=list)

    def complete(self, system: str, messages: list[Message], tools: list[dict]) -> LLMResponse:
        self.calls.append({"system": system, "messages": copy.deepcopy(messages), "tools": copy.deepcopy(tools)})
        i = min(len(self.calls) - 1, len(self.steps) - 1)
        step = self.steps[i]
        return step(messages) if callable(step) else step

    def last_tool_results(self) -> list[Block]:
        """tool_result blocks of the most recent user message the model was shown."""
        if not self.calls:
            return []
        for m in reversed(self.calls[-1]["messages"]):
            if m["role"] == "user" and isinstance(m["content"], list):
                return [b for b in m["content"] if b.get("type") == "tool_result"]
        return []
