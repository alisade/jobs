"""Hidden-test helpers: an independent strict fake API and a scriptable toolbox, so the
grade does not depend on files the learner could have edited."""

from __future__ import annotations

import asyncio
import copy
import json
from pathlib import Path
from typing import Any

from ait1_hidden_fakeapi import FakeAnthropic

from agentloop import loop

HERE = Path(__file__).resolve().parent
SECRET_HOST = "inventory-svc.prod.lumen.internal:8443"


def recorded_turns() -> list[dict[str, Any]]:
    path = HERE / "ait1_recorded_turns.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def use(tid: str, name: str, **inp: Any) -> dict[str, Any]:
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


def text(t: str) -> dict[str, Any]:
    return {"type": "text", "text": t}


def tool_round(*blocks: dict[str, Any]) -> dict[str, Any]:
    return {"content": list(blocks), "stop_reason": "tool_use"}


def final(t: str = "Done.") -> dict[str, Any]:
    return {"content": [text(t)], "stop_reason": "end_turn"}


class ScriptedTools:
    """``spec`` maps tool name to {"delay": s, "error": Exception instance, "output": str}."""

    def __init__(self, spec: dict[str, dict[str, Any]]):
        self.spec = spec
        self.calls: list[str] = []

    async def call(self, name: str, tool_input: dict[str, Any]) -> str:
        self.calls.append(name)
        if name not in self.spec:
            raise KeyError(f"unknown tool {name}")
        s = self.spec[name]
        if s.get("delay"):
            await asyncio.sleep(s["delay"])
        if s.get("error") is not None:
            raise s["error"]
        return s.get("output", f"{name} ok")


async def run(script, tools, *, rate_limit_calls=None, tool_timeout_s=0.5):
    client = FakeAnthropic(copy.deepcopy(script), rate_limit_calls)
    messages = [{"role": "user", "content": "Is the lamp in stock and when can it arrive?"}]
    result = await loop.run_turn(
        client, tools, messages, turn_id="t-hidden", tool_timeout_s=tool_timeout_s, retry_base_s=0.001
    )
    return result, client


def results_after(client, tool_round_index: int) -> list[dict[str, Any]]:
    """The user message the loop sent back after the n-th tool round (0-based), as the API
    received it on the following request."""
    request = client.messages.requests[tool_round_index + 1]
    return request["messages"][-1]["content"]
