"""Metrics for one control's eval set. Pure functions over plain dicts.

The helpers at the top are complete; every function marked TODO is yours. The README defines each
metric exactly (denominators, tie-breaks, percentile method): the hidden tests check those definitions."""

from __future__ import annotations

import math
from collections import Counter

ATTRIBUTES = ["approval_before_deploy", "independent_approver", "linked_change", "tests_passed"]
FIELDS = ATTRIBUTES + ["overall"]
# tie-break order for the modal value: the more severe outcome wins
SEVERITY = {"exception": 0, "needs_review": 1, "not_evaluable": 1, "pass": 2}


def value_of(row: dict, field: str) -> str | None:
    """Outcome of a run row or a label row for an attribute or 'overall'."""
    if field == "overall":
        return row.get("overall")
    src = row.get("outputs", row.get("labels")) or {}
    return src.get(field)


def scored_rows(labels: dict[str, dict], runs: list[dict]) -> list[dict]:
    """Run rows that have a label, first occurrence of each (sample_id, run) only."""
    seen, out = set(), []
    for r in runs:
        key = (r["sample_id"], r["run"])
        if key in seen or r["sample_id"] not in labels:
            continue
        seen.add(key)
        out.append(r)
    return out


def accuracy(labels: dict[str, dict], runs: list[dict], field: str) -> float | None:
    raise NotImplementedError("TODO: README task 1 (accuracy)")


def exception_scores(labels: dict[str, dict], runs: list[dict], field: str) -> dict:
    raise NotImplementedError("TODO: README task 1 (exception_scores)")


def modal(values: list[str]) -> tuple[str, int]:
    raise NotImplementedError("TODO: README task 1 (modal)")


def _by_sample(runs: list[dict], field: str) -> dict[str, list[str]]:
    seen, by = set(), {}
    for r in runs:
        key = (r["sample_id"], r["run"])
        if key in seen:
            continue
        seen.add(key)
        by.setdefault(r["sample_id"], []).append(value_of(r, field))
    return by


def agreement(runs: list[dict], field: str = "overall") -> dict:
    raise NotImplementedError("TODO: README task 1 (agreement)")


def fleiss_kappa(runs: list[dict], field: str = "overall", n_runs: int = 5) -> dict:
    raise NotImplementedError("TODO: README task 1 (fleiss_kappa)")


def run_cost(row: dict, prices: dict) -> float:
    raise NotImplementedError("TODO: README task 1 (run_cost)")


def cost(runs: list[dict], prices: dict) -> dict:
    raise NotImplementedError("TODO: README task 1 (cost)")


def percentile(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile: the value at 1-based rank ceil(p/100 * n) of the sorted values."""
    raise NotImplementedError("TODO: README task 1 (percentile)")


def latency(runs: list[dict]) -> dict:
    raise NotImplementedError("TODO: README task 1 (latency)")
