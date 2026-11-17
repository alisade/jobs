"""Offline replay of a recorded assistant session: the recorded model turns are re-issued against the
CURRENT tool code, so you can see what the tools return now. No model, no network."""

from __future__ import annotations

import json
import pathlib

from .session import Session
from .tools import call_tool


def load(path: str) -> dict:
    return json.loads(pathlib.Path(path).read_text())


def replay(path: str) -> list[dict]:
    t = load(path)
    s = t["session"]
    session = Session(agent_id=s["agent_id"], user_id=s["user_id"], tenant_id=s["tenant_id"], trace_id=s["trace_id"])
    out = []
    for turn in t["model_turns"]:
        out.append({"tool": turn["tool"], "args": turn["args"], "result": call_tool(session, turn["tool"], dict(turn["args"]))})
    return out


if __name__ == "__main__":
    import sys
    for step in replay(sys.argv[1] if len(sys.argv) > 1 else "transcripts/inc-7731.json"):
        print(json.dumps(step, indent=1))
