"""Metrics for one control's eval set. Pure functions over plain dicts (see README for definitions)."""

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
    rows = scored_rows(labels, runs)
    if not rows:
        return None
    ok = sum(1 for r in rows if value_of(r, field) == value_of(labels[r["sample_id"]], field))
    return ok / len(rows)


def exception_scores(labels: dict[str, dict], runs: list[dict], field: str) -> dict:
    tp = fp = fn = 0
    for r in scored_rows(labels, runs):
        truth = value_of(labels[r["sample_id"]], field) == "exception"
        pred = value_of(r, field) == "exception"
        tp += truth and pred
        fp += (not truth) and pred
        fn += truth and not pred
    return {
        "tp": tp, "fp": fp, "fn": fn, "support": tp + fn,
        "recall": tp / (tp + fn) if tp + fn else None,
        "precision": tp / (tp + fp) if tp + fp else None,
    }


def modal(values: list[str]) -> tuple[str, int]:
    c = Counter(values)
    best = sorted(c.items(), key=lambda kv: (-kv[1], SEVERITY.get(kv[0], 9), kv[0]))[0]
    return best


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
    by = _by_sample(runs, field)
    if not by:
        return {"mean_modal_agreement": None, "fully_consistent_share": None, "samples": 0}
    rates = [modal(v)[1] / len(v) for v in by.values()]
    full = sum(1 for v in by.values() if len(set(v)) == 1)
    return {"mean_modal_agreement": sum(rates) / len(rates), "fully_consistent_share": full / len(by), "samples": len(by)}


def fleiss_kappa(runs: list[dict], field: str = "overall", n_runs: int = 5) -> dict:
    subjects = [v for v in _by_sample(runs, field).values() if len(v) == n_runs]
    if not subjects or n_runs < 2:
        return {"kappa": None, "subjects": len(subjects)}
    cats = sorted({x for v in subjects for x in v})
    N, n = len(subjects), n_runs
    counts = [[v.count(c) for c in cats] for v in subjects]
    p_j = [sum(row[j] for row in counts) / (N * n) for j in range(len(cats))]
    P_i = [(sum(x * x for x in row) - n) / (n * (n - 1)) for row in counts]
    P_bar = sum(P_i) / N
    P_e = sum(p * p for p in p_j)
    if P_e == 1:
        return {"kappa": 1.0, "subjects": N}
    return {"kappa": (P_bar - P_e) / (1 - P_e), "subjects": N}


def run_cost(row: dict, prices: dict) -> float:
    u = row.get("usage") or {}
    p = prices["per_1m_usd"]
    prompt, cached, out = u.get("prompt_tokens", 0), u.get("cached_tokens", 0), u.get("output_tokens", 0)
    return ((prompt - cached) * p["input"] + cached * p["cached_input"] + out * p["output"]) / 1_000_000


def cost(runs: list[dict], prices: dict) -> dict:
    if not runs:
        return {"total_usd": 0.0, "per_100_samples_usd": None, "runs": 0}
    total = sum(run_cost(r, prices) for r in runs)
    return {"total_usd": total, "per_100_samples_usd": 100 * total / len(runs), "runs": len(runs)}


def percentile(values: list[float], p: float) -> float | None:
    """Nearest-rank percentile: the value at 1-based rank ceil(p/100 * n) of the sorted values."""
    if not values:
        return None
    s = sorted(values)
    rank = max(1, math.ceil(p / 100 * len(s)))
    return s[rank - 1]


def latency(runs: list[dict]) -> dict:
    vals = [r["latency_ms"] for r in runs if r.get("latency_ms") is not None]
    return {"p50_ms": percentile(vals, 50), "p95_ms": percentile(vals, 95), "runs": len(vals)}
