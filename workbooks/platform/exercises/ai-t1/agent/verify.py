"""Verification gate between the agent and the pull request."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Verdict:
    ok: bool
    counts: dict
    reasons: list = field(default_factory=list)


def summarize(plan: dict) -> dict:
    """Counts for a terraform show -json plan: import, add, change, destroy, replace."""
    raise NotImplementedError("summarize is not used by the current gate")


def verify(plan_json_path: str | Path, model_summary: dict | None = None) -> Verdict:
    s = model_summary or {}
    counts = {"import": s.get("to_import", 0), "add": s.get("to_add", 0),
              "change": s.get("to_change", 0), "destroy": s.get("to_destroy", 0), "replace": 0}
    ok = counts["import"] > 0 and counts["add"] == 0 and counts["change"] == 0 and counts["destroy"] == 0
    return Verdict(ok, counts, [] if ok else ["plan is not import-only"])
