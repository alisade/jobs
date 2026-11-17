"""Builds the Messages API request for each turn of the headless migration agent (runs in CI, one
job per module). See README.md for what the request must look like."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

MODEL = "claude-sonnet-4-5"
SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

TOOLS = [
    {"name": "read_file", "description": "Read a file from the module checkout.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "search", "description": "Regex search over the module checkout.",
     "input_schema": {"type": "object", "properties": {"pattern": {"type": "string"}}, "required": ["pattern"]}},
    {"name": "propose_patch", "description": "Propose a full-file patch for human review.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                      "required": ["path", "content"]}},
]

INSTRUCTIONS = """You are the ClaimDesk modernization agent. You work on one Maven module at a time.
Follow the skills below exactly. Never edit tests or golden files. Stop and ask for approval at every
major version change. Every claim you make cites a file and line."""


def load_skills() -> dict[str, str]:
    return {p.stem: p.read_text() for p in SKILLS_DIR.glob("*.md")}


def build_request(task: str, repo_files: Iterable[str], skills: dict[str, str], now: datetime,
                  history: list[dict]) -> dict:
    """Return the request body for one turn. history holds the conversation so far (user/assistant turns)."""
    listing = "\n".join(repo_files)
    skill_text = "\n\n".join(skills.values())
    system_text = (
        f"{INSTRUCTIONS}\n\nCurrent time: {now.isoformat(timespec='seconds')} (use it in your change log).\n\n"
        f"Repository files:\n{listing}\n\nSkills:\n{skill_text}"
    )
    return {
        "model": MODEL,
        "max_tokens": 4096,
        "tools": TOOLS,
        "system": [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": task}, *history],
    }
