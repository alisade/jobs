"""Tool definitions (JSON Schema, as sent to the model) and their implementations over a workspace."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TOOLS: list[dict] = [
    {
        "name": "read_file",
        "description": "Read a UTF-8 text file from the repository. path is relative to the repository root.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "minLength": 1}},
            "required": ["path"],
            "additionalProperties": False,
        },
    },
    {
        "name": "search",
        "description": "Search the repository for a regular expression. Returns path:line: text for each match.",
        "input_schema": {
            "type": "object",
            "properties": {"pattern": {"type": "string", "minLength": 1, "maxLength": 200}},
            "required": ["pattern"],
            "additionalProperties": False,
        },
    },
    {
        "name": "propose_patch",
        "description": "Replace the full content of one file. A human reviewer approves or rejects every patch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "minLength": 1},
                "content": {"type": "string"},
                "reason": {"type": "string", "minLength": 10},
            },
            "required": ["path", "content", "reason"],
            "additionalProperties": False,
        },
    },
]


@dataclass(frozen=True)
class PatchRequest:
    path: str
    content: str
    reason: str


def read_file(root: Path, path: str) -> str:
    return (root / path).read_text(encoding="utf8")


def search(root: Path, pattern: str) -> str:
    rx = re.compile(pattern)
    out = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            for n, line in enumerate(p.read_text(encoding="utf8", errors="replace").splitlines(), 1):
                if rx.search(line):
                    out.append(f"{p.relative_to(root).as_posix()}:{n}: {line.strip()}")
    return "\n".join(out) or "(no matches)"


def write_file(root: Path, path: str, content: str) -> str:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf8")
    return f"wrote {path} ({len(content)} chars)"
