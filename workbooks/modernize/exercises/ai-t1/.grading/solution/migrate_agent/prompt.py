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
    return {p.stem: p.read_text() for p in sorted(SKILLS_DIR.glob("*.md"))}


def build_request(task: str, repo_files: Iterable[str], skills: dict[str, str], now: datetime,
                  history: list[dict]) -> dict:
    """Return the request body for one turn. history holds the conversation so far (user/assistant turns).

    Prompt caching matches the prefix byte for byte (tools, then system, then messages, up to the last
    cache_control breakpoint). So everything before the breakpoint must be identical on every turn and
    across CI processes: instructions, the file listing (sorted: it comes from a set), and the skills
    (sorted by name: glob order is filesystem order). Anything that changes per turn, such as the
    current time, goes after the breakpoint.
    """
    listing = "\n".join(sorted(set(repo_files)))
    skill_text = "\n\n".join(skills[name] for name in sorted(skills))
    static_text = f"{INSTRUCTIONS}\n\nRepository files:\n{listing}\n\nSkills:\n{skill_text}"
    dynamic_text = f"Current time: {now.isoformat(timespec='seconds')} (use it in your change log)."
    return {
        "model": MODEL,
        "max_tokens": 4096,
        "tools": TOOLS,
        "system": [
            {"type": "text", "text": static_text, "cache_control": {"type": "ephemeral"}},
            {"type": "text", "text": dynamic_text},
        ],
        "messages": [{"role": "user", "content": task}, *history],
    }
