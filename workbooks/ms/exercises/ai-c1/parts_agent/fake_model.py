"""Fake model client that replays scripted turns. Provided.

Response shape (a subset of a Messages-API style response):
  {"content": [{"type": "text", "text": "..."},
               {"type": "tool_use", "id": "toolu_1", "name": "get_quote", "input": {...}}],
   "stop_reason": "end_turn" | "tool_use" | "max_tokens",
   "usage": {"input_tokens": 812, "output_tokens": 64}}
No network, no API key: the script decides what the "model" says, including bad decisions.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path


class ScriptExhausted(AssertionError):
    pass


class FakeModelClient:
    def __init__(self, script: list[dict]):
        self.script = copy.deepcopy(list(script))
        self.requests: list[dict] = []

    @classmethod
    def from_file(cls, path: str | Path) -> "FakeModelClient":
        return cls(json.loads(Path(path).read_text())["turns"])

    def create(self, *, model: str, system: str, messages: list[dict], tools: list[dict],
               max_tokens: int) -> dict:
        self.requests.append(copy.deepcopy({"model": model, "system": system, "messages": messages,
                                            "tools": tools, "max_tokens": max_tokens}))
        if not self.script:
            raise ScriptExhausted("the model script has no more turns")
        return copy.deepcopy(self.script.pop(0))


def text(t: str) -> dict:
    return {"type": "text", "text": t}


def tool_use(id_: str, name: str, input_: dict) -> dict:
    return {"type": "tool_use", "id": id_, "name": name, "input": input_}


def turn(*blocks: dict, stop: str = "tool_use", usage: tuple[int, int] = (500, 40)) -> dict:
    return {"content": list(blocks), "stop_reason": stop,
            "usage": {"input_tokens": usage[0], "output_tokens": usage[1]}}
