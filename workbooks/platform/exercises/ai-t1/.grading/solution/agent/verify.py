"""Verification gate between the agent and the pull request.

The gate trusts the plan file, never the model: counts are computed from the full
terraform show -json output, and anything it cannot read or understand fails closed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Verdict:
    ok: bool
    counts: dict
    reasons: list = field(default_factory=list)
    replaced: list = field(default_factory=list)
    destroyed: list = field(default_factory=list)


def summarize(plan: dict) -> dict:
    """Counts like terraform's summary line: a replace counts as one add and one destroy."""
    c = {"import": 0, "add": 0, "change": 0, "destroy": 0, "replace": 0}
    replaced, destroyed, changed = [], [], []
    for rc in plan["resource_changes"]:
        if rc.get("mode", "managed") != "managed":
            continue
        ch = rc["change"]
        actions = list(ch["actions"])
        if ch.get("importing") is not None:
            c["import"] += 1
        if actions in (["delete", "create"], ["create", "delete"]):
            c["replace"] += 1
            c["add"] += 1
            c["destroy"] += 1
            replaced.append(rc["address"])
        elif actions == ["create"]:
            c["add"] += 1
        elif actions == ["update"]:
            c["change"] += 1
            changed.append(rc["address"])
        elif actions == ["delete"]:
            c["destroy"] += 1
            destroyed.append(rc["address"])
        elif actions not in (["no-op"], ["read"]):
            raise ValueError(f"unknown actions {actions} for {rc['address']}")
    return {"counts": c, "replaced": replaced, "destroyed": destroyed, "changed": changed}


def verify(plan_json_path: str | Path, model_summary: dict | None = None) -> Verdict:
    """model_summary is accepted for logging only; it never influences the verdict."""
    empty = {"import": 0, "add": 0, "change": 0, "destroy": 0, "replace": 0}
    try:
        plan = json.loads(Path(plan_json_path).read_text())
        if not isinstance(plan, dict) or not isinstance(plan.get("resource_changes"), list):
            raise ValueError("no resource_changes list")
        if plan.get("errored") or plan.get("complete") is False:
            raise ValueError("plan errored or is incomplete")
        s = summarize(plan)
    except (OSError, ValueError, KeyError, TypeError) as e:
        return Verdict(False, empty, [f"cannot verify plan: {e}"])
    c = s["counts"]
    reasons = []
    if c["import"] == 0:
        reasons.append("no imports in the plan")
    if c["add"] or c["change"] or c["destroy"]:
        reasons.append(f"plan is not import-only: {c['add']} to add, {c['change']} to change, "
                       f"{c['destroy']} to destroy, replaced: {s['replaced']}")
    if model_summary is not None:
        claim = {k: model_summary.get(f"to_{k}") for k in ("import", "add", "change", "destroy")}
        if any(claim[k] is not None and claim[k] != c[k] for k in claim):
            reasons.append(f"model summary {claim} disagrees with the plan; using the plan")
    blocking = [r for r in reasons if not r.startswith("model summary")]
    return Verdict(not blocking, c, reasons, s["replaced"], s["destroyed"])
