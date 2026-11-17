"""Layered eval gate for the PA assistant. Implement the TODOs (README has the exact rules)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import ValidationError  # noqa: F401

from .schema import Output  # noqa: F401


def load_runs(run_dir: str | Path) -> list[list[dict]]:
    return [json.loads(p.read_text()) for p in sorted(Path(run_dir).glob("run*.json"))]


def wilson_lower(successes: int, n: int, z: float = 1.96) -> float:
    raise NotImplementedError  # TODO


def p95(values: list[float]) -> float:
    raise NotImplementedError  # TODO: nearest-rank


def evaluate(run_dir, cases: list[dict], policy: dict[str, str], baseline: dict) -> dict:
    """Return {"runs", "gates": {name: {"value", "threshold", "passed", ...}}, "passed", "cost_usd_per_run", "p95_latency_ms"}.

    First draft from the hackathon: mean "approve" agreement with gold, nothing else.
    """
    runs = load_runs(run_dir)
    gold = {c["case_id"]: c for c in cases}
    agree = n = 0
    for rows in runs:
        for row in rows:
            out = json.loads(row["output"])
            n += 1
            agree += int((out["route"] == "auto") == (gold[row["case_id"]]["gold_route"] == "auto"))
    acc = agree / max(1, n)
    gates = {"route_accuracy": {"value": acc, "threshold": 0.8, "passed": acc >= 0.8}}
    return {"runs": len(runs), "gates": gates, "passed": acc >= 0.8, "cost_usd_per_run": 0.0, "p95_latency_ms": 0}


def summary_md(report: dict) -> str:
    return f"eval gate: {'PASS' if report['passed'] else 'FAIL'}\n"  # TODO: table per gate, cost, latency


def main(argv: list[str]) -> int:
    """python -m evals.gates <run_dir> <fixtures_dir> [summary.md]"""
    run_dir, fix = Path(argv[1]), Path(argv[2])
    report = evaluate(run_dir, json.loads((fix / "cases.json").read_text()), json.loads((fix / "policy.json").read_text()),
                      json.loads((fix / "baseline.json").read_text()))
    md = summary_md(report)
    if len(argv) > 3:
        Path(argv[3]).write_text(md)
    print(md)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
