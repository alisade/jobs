"""Fake LLM client that replays recorded Messages-API-shaped responses (no network, no API key).

Each recording (data/recordings/<scenario>.json) is a list of turns:
  {"expect": {...optional checks on what the agent sent...}, "response": {"content": [...], "stop_reason": "..."}}

Response content blocks use the Anthropic Messages shapes:
  {"type": "text", "text": "..."}
  {"type": "tool_use", "id": "toolu_...", "name": "...", "input": {...}}
stop_reason is "tool_use" or "end_turn".

`expect` lets a recording check that the agent behaved as the recorded model saw it:
  "tool_results": [{"tool_use_id": "...", "is_error": true|false}]   blocks in the last user message
  "user_text_contains": "..."                                         substring of the last user message text
  "tools_offered": ["get_alert", ...]                                 names that must be in the tools list
If the agent diverges, create() raises TranscriptDiverged: the recorded model would not have produced
the next response for a different conversation.
"""

from __future__ import annotations

import copy
import json
import pathlib

RECORDINGS = pathlib.Path(__file__).resolve().parents[1] / "data" / "recordings"


class TranscriptDiverged(AssertionError):
    pass


class RecordingExhausted(RuntimeError):
    pass


def _last_user(messages: list[dict]) -> dict:
    for m in reversed(messages):
        if m["role"] == "user":
            return m
    return {"role": "user", "content": []}


def _blocks(msg: dict) -> list[dict]:
    c = msg.get("content")
    if isinstance(c, str):
        return [{"type": "text", "text": c}]
    return list(c or [])


class FakeLLM:
    def __init__(self, turns: list[dict], name: str = "inline") -> None:
        self.turns = turns
        self.name = name
        self.calls: list[dict] = []

    @classmethod
    def from_scenario(cls, scenario: str) -> "FakeLLM":
        data = json.loads((RECORDINGS / f"{scenario}.json").read_text())
        return cls(data["turns"], scenario)

    def create(self, *, system: str, messages: list[dict], tools: list[dict], max_tokens: int = 1024) -> dict:
        i = len(self.calls)
        self.calls.append({"system": system, "messages": copy.deepcopy(messages), "tools": copy.deepcopy(tools)})
        if i >= len(self.turns):
            raise RecordingExhausted(f"{self.name}: no recorded response for turn {i + 1}")
        turn = self.turns[i]
        exp = turn.get("expect") or {}
        last = _last_user(messages)
        if "tools_offered" in exp:
            names = {t["name"] for t in tools}
            missing = set(exp["tools_offered"]) - names
            if missing:
                raise TranscriptDiverged(f"{self.name} turn {i + 1}: tools not offered: {sorted(missing)}")
        if "tool_results" in exp:
            got = {b.get("tool_use_id"): bool(b.get("is_error", False)) for b in _blocks(last) if b.get("type") == "tool_result"}
            for want in exp["tool_results"]:
                tid = want["tool_use_id"]
                if tid not in got:
                    raise TranscriptDiverged(f"{self.name} turn {i + 1}: no tool_result for {tid}")
                if got[tid] != bool(want.get("is_error", False)):
                    raise TranscriptDiverged(f"{self.name} turn {i + 1}: tool_result {tid} is_error={got[tid]}, recording expects {want.get('is_error', False)}")
        if "user_text_contains" in exp:
            text = " ".join(b.get("text", "") if b.get("type") == "text" else str(b.get("content", "")) for b in _blocks(last))
            if exp["user_text_contains"].lower() not in text.lower():
                raise TranscriptDiverged(f"{self.name} turn {i + 1}: last user message lacks {exp['user_text_contains']!r}")
        return copy.deepcopy(turn["response"])
