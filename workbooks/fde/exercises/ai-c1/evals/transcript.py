"""Recorded transcripts and the flattened event view the checks read. Given; do not change.

A transcript file is one run of one scenario, recorded from the shopping agent's
Messages API runtime (commerce-agents, retail vertical) with the request's ``messages``
array as sent on the last round, plus the final assistant message:

    {"scenario": "return-window", "run": 2, "messages": [
        {"role": "user", "content": "What's your return window?"},
        {"role": "assistant", "content": [
            {"type": "text", "text": "Let me check."},
            {"type": "tool_use", "id": "toolu_01", "name": "search_policies",
             "input": {"query": "returns"}}]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_01", "content": "...",
             "is_error": false}]},
        {"role": "assistant", "content": [{"type": "text", "text": "You have 30 days."}]}]}

``events(t)`` flattens that into one ordered list, which is what every check walks.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

EventKind = Literal["user_text", "assistant_text", "tool_use", "tool_result"]


@dataclass(frozen=True)
class Transcript:
    scenario: str
    run: int
    messages: list[dict[str, Any]]


@dataclass(frozen=True)
class Event:
    """One block, in transcript order. ``name`` is the tool name on tool_use AND on
    tool_result (resolved through ``tool_use_id``); ``text`` is the text of a text block or
    the normalized content of a tool_result."""

    index: int
    kind: EventKind
    text: str = ""
    name: str = ""
    tool_use_id: str = ""
    input: dict[str, Any] = field(default_factory=dict)
    is_error: bool = False


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str = ""
    errored: bool = False  # the check itself could not run (e.g. the judge had no verdict)


def _result_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
    return "" if content is None else str(content)


def events(t: Transcript) -> list[Event]:
    out: list[Event] = []
    names: dict[str, str] = {}
    for message in t.messages:
        role, content = message["role"], message["content"]
        if isinstance(content, str):
            kind = "user_text" if role == "user" else "assistant_text"
            out.append(Event(index=len(out), kind=kind, text=content))
            continue
        for block in content:
            btype = block.get("type")
            if btype == "text":
                kind = "user_text" if role == "user" else "assistant_text"
                out.append(Event(index=len(out), kind=kind, text=block.get("text", "")))
            elif btype == "tool_use":
                names[block["id"]] = block["name"]
                out.append(
                    Event(
                        index=len(out),
                        kind="tool_use",
                        name=block["name"],
                        tool_use_id=block["id"],
                        input=dict(block.get("input") or {}),
                    )
                )
            elif btype == "tool_result":
                tid = block["tool_use_id"]
                out.append(
                    Event(
                        index=len(out),
                        kind="tool_result",
                        name=names.get(tid, ""),
                        tool_use_id=tid,
                        text=_result_text(block.get("content")),
                        is_error=bool(block.get("is_error", False)),
                    )
                )
    return out


def load_transcript(path: Path) -> Transcript:
    data = json.loads(Path(path).read_text())
    return Transcript(scenario=data["scenario"], run=int(data["run"]), messages=data["messages"])


def load_transcripts(directory: Path) -> list[Transcript]:
    return [load_transcript(p) for p in sorted(Path(directory).glob("*.json"))]
