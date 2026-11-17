"""Build the Converse request for one help desk turn.

3.1.0 (2026-11-10): the model now gets the current time (it kept getting "is my approval still
valid" wrong) and support asked for the request id in the prompt so they can correlate
transcripts with logs.
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
    system = [
        {"text": SYSTEM + f"\nCurrent time: {stamp}. Request id: {request_id}. Signed-in user: {user}.\n"},
        {"cachePoint": {"type": "default"}},
    ]
    tools = [tool_spec(n) for n in tool_names]
    messages = list(history or []) + [{"role": "user", "content": [{"text": question}]}]
    return {"modelId": MODEL, "system": system, "toolConfig": {"tools": tools}, "messages": messages,
            "inferenceConfig": {"maxTokens": 1024}}
