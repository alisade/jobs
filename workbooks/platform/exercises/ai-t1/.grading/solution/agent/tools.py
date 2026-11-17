"""Tools the import agent can call."""

from __future__ import annotations

import json
from pathlib import Path

from .verify import summarize

MAX_TOOL_OUTPUT = 8000  # keep tool results inside the context budget


def terraform_plan(plan_json_path: str | Path) -> str:
    """Return a compact, complete summary of the plan instead of raw JSON that would be truncated."""
    try:
        plan = json.loads(Path(plan_json_path).read_text())
        s = summarize(plan)
    except (OSError, ValueError, KeyError, TypeError) as e:
        return json.dumps({"error": f"cannot read plan: {e}"})
    out = {"counts": s["counts"], "replaced": s["replaced"], "destroyed": s["destroyed"], "changed": s["changed"]}
    text = json.dumps(out)
    if len(text) > MAX_TOOL_OUTPUT:  # never cut JSON mid-way: drop lists, keep counts, say so
        text = json.dumps({"counts": s["counts"], "truncated_lists": True})
    return text
