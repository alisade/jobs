"""Helpers for scripted runs: build Messages-API-shaped responses."""

import shutil
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "workspace"


def workspace(tmp_path: Path) -> Path:
    dst = tmp_path / "repo"
    shutil.copytree(FIXTURE, dst)
    return dst


def use(id_, name, **inp):
    return {"type": "tool_use", "id": id_, "name": name, "input": inp}


def tools(*blocks, text="Working on it."):
    return {"stop_reason": "tool_use", "content": [{"type": "text", "text": text}, *blocks]}


def end(text="Done."):
    return {"stop_reason": "end_turn", "content": [{"type": "text", "text": text}]}


def results(model, call_index):
    """tool_result blocks the loop sent on model call number call_index (0-based)."""
    return model.calls[call_index]["messages"][-1]["content"]


class Approver:
    def __init__(self, answer=True):
        self.answer = answer
        self.seen = []

    def __call__(self, req):
        self.seen.append(req)
        return self.answer
