"""ScriptedModel: an offline Strands model provider that replays a script (works as shipped).

Each step is {"tool": name, "input": {...}} (the model asks for a tool) or {"text": "..."} (final
answer). One step is consumed per model call. Every call records the messages it was given in
``self.seen`` so tests can check what the model saw, and reports fixed token usage.
"""
from __future__ import annotations

import json
from typing import Any

from strands.models.model import Model


class ScriptExhausted(RuntimeError):
    pass


class ScriptedModel(Model):
    def __init__(self, script: list[dict], input_tokens: int = 100, output_tokens: int = 20):
        self.script = list(script)
        self.calls = 0
        self.seen: list[list[dict]] = []
        self.tool_specs_seen: list[list[str]] = []
        self.config: dict[str, Any] = {"model_id": "scripted"}
        self.usage = (input_tokens, output_tokens)

    def update_config(self, **kw: Any) -> None:
        self.config.update(kw)

    def get_config(self) -> Any:
        return self.config

    async def structured_output(self, output_model, prompt, system_prompt=None, **kw):  # pragma: no cover
        raise NotImplementedError("not used in these exercises")
        yield

    async def stream(self, messages, tool_specs=None, system_prompt=None, **kwargs):
        if self.calls >= len(self.script):
            raise ScriptExhausted(f"model script exhausted after {self.calls} calls")
        step = self.script[self.calls]
        self.calls += 1
        self.seen.append(json.loads(json.dumps(messages, default=str)))
        self.tool_specs_seen.append([t["name"] for t in (tool_specs or [])])
        yield {"messageStart": {"role": "assistant"}}
        if "tool" in step:
            tid = f"tooluse-{id(self) % 10000}-{self.calls}"
            yield {"contentBlockStart": {"start": {"toolUse": {"toolUseId": tid, "name": step["tool"]}}}}
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": json.dumps(step.get("input", {}))}}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            yield {"contentBlockDelta": {"delta": {"text": step["text"]}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}
        i, o = self.usage
        yield {"metadata": {"usage": {"inputTokens": i, "outputTokens": o, "totalTokens": i + o},
                            "metrics": {"latencyMs": 3}}}


def tool_results(model: ScriptedModel) -> list[dict]:
    """All toolResult blocks the model has been shown so far (from the last call's history)."""
    out = []
    if not model.seen:
        return out
    for msg in model.seen[-1]:
        for block in msg.get("content", []):
            if "toolResult" in block:
                out.append(block["toolResult"])
    return out
