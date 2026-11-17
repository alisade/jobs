"""Tools the import agent can call."""

from __future__ import annotations

from pathlib import Path

MAX_TOOL_OUTPUT = 8000  # keep tool results inside the context budget


def terraform_plan(plan_json_path: str | Path) -> str:
    """Return the plan (terraform show -json output) for the model to read."""
    text = Path(plan_json_path).read_text()
    return text[:MAX_TOOL_OUTPUT]
