"""Build the Converse request for one help desk turn.

Cache layout: everything before the cache point must be byte-identical across requests, so it
holds only static content: the tool specs (sorted by name, so plugin load order cannot change
the bytes) and the system prompt. Per-request data (time, request id, user) goes after the
cache point, in the first user message of the turn, where it still reaches the model.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from .tools import tool_spec

SYSTEM = (Path(__file__).resolve().parent.parent / "prompts" / "system.md").read_text()
MODEL = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


def build_request(user: str, question: str, request_id: str, now: float, tool_names: list[str],
                  history: list[dict] | None = None) -> dict:
    stamp = dt.datetime.fromtimestamp(now, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    system = [{"text": SYSTEM}, {"cachePoint": {"type": "default"}}]
    tools = [tool_spec(n) for n in sorted(tool_names)]
    context = f"<context>Current time: {stamp}. Request id: {request_id}. Signed-in user: {user}.</context>"
    messages = list(history or []) + [{"role": "user", "content": [{"text": context}, {"text": question}]}]
    return {"modelId": MODEL, "system": system, "toolConfig": {"tools": tools}, "messages": messages,
            "inferenceConfig": {"maxTokens": 1024}}
