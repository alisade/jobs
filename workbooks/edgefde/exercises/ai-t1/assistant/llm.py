"""Stub LLM client that replays recorded responses (complete: do not edit).

The response shape is a simplified OpenAI-compatible chat turn, the same shape Ollama and the
llama.cpp server return on their OpenAI-compatible endpoints:

    {"role": "assistant", "tool_calls": [{"id": "c1", "name": "get_alerts", "arguments": {...}}]}
    {"role": "assistant", "content": "<text, for the final answer a JSON object>"}

Messages you send are a list of dicts: {"role": "system"|"user"|"assistant"|"tool", ...}; a tool
result is {"role": "tool", "tool_call_id": "c1", "content": "<json string>"}.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field


class ScriptExhausted(RuntimeError):
    pass


@dataclass
class StubLLM:
    name: str
    script: list[dict]
    latency_ms: float = 100.0
    calls: list[dict] = field(default_factory=list)

    def chat(self, messages: list[dict], tools: list[dict]) -> dict:
        self.calls.append({"messages": copy.deepcopy(messages), "tools": copy.deepcopy(tools)})
        if len(self.calls) > len(self.script):
            raise ScriptExhausted(f"{self.name}: no recorded response for call {len(self.calls)}")
        return copy.deepcopy(self.script[len(self.calls) - 1])
