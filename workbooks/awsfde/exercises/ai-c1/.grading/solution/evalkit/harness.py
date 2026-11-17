"""Run the golden cases over recorded runs, build the report, gate the release."""

from __future__ import annotations

from typing import Callable

from .checks import ALL

Judge = Callable[[dict, dict], bool]


def evaluate(golden: list[dict], runs: list[dict], judge: Judge | None = None) -> dict:
    by_case: dict[str, list[dict]] = {}
    for r in runs:
        by_case.setdefault(r["case_id"], []).append(r)
    unknown = sorted(set(by_case) - {c["id"] for c in golden})
    if unknown:
        raise ValueError(f"runs for unknown cases: {unknown}")
    per_case, per_check = [], {k: 0 for k in ALL}
    if judge is not None:
        per_check["judge"] = 0
    isolation, costs = [], []
    for case in golden:
        rs = sorted(by_case.get(case["id"], []), key=lambda r: r["run"])
        if not rs:
            per_case.append({"id": case["id"], "kind": case["kind"], "runs": 0, "passed_runs": 0,
                             "pass": False, "flaky": False, "failures": [{"run": None, "check": "missing", "reason": "no runs"}]})
            continue
        failures, passed_runs = [], 0
        for r in rs:
            costs.append(float(r.get("cost_usd", 0.0)))
            run_ok = True
            for name, fn in ALL.items():
                why = fn(case, r)
                if why:
                    run_ok = False
                    per_check[name] += 1
                    failures.append({"run": r["run"], "check": name, "reason": why})
                    if name == "tenant_isolation":
                        isolation.append({"id": case["id"], "run": r["run"], "reason": why})
            if judge is not None and not judge(case, r):
                run_ok = False
                per_check["judge"] += 1
                failures.append({"run": r["run"], "check": "judge", "reason": "judge rejected the answer"})
            passed_runs += run_ok
        per_case.append({"id": case["id"], "kind": case["kind"], "runs": len(rs), "passed_runs": passed_runs,
                         "pass": passed_runs == len(rs), "flaky": 0 < passed_runs < len(rs), "failures": failures})
    n = len(per_case)
    return {
        "cases": n,
        "pass_rate": round(sum(c["pass"] for c in per_case) / n, 4) if n else 0.0,
        "consistency": round(sum(c["passed_runs"] for c in per_case) / max(1, sum(c["runs"] for c in per_case)), 4),
        "per_check": per_check,
        "flaky": [c["id"] for c in per_case if c["flaky"]],
        "isolation_failures": isolation,
        "cost": {"mean_per_run": round(sum(costs) / len(costs), 6) if costs else 0.0,
                 "max_per_run": round(max(costs), 6) if costs else 0.0},
        "per_case": per_case,
    }


def regressions(baseline: dict, candidate: dict) -> list[str]:
    before = {c["id"]: c["pass"] for c in baseline["per_case"]}
    return sorted(c["id"] for c in candidate["per_case"] if before.get(c["id"]) and not c["pass"])


def gate(report: dict, baseline: dict | None = None, min_pass_rate: float = 0.9) -> tuple[bool, list[str]]:
    reasons = []
    if report["isolation_failures"]:
        reasons.append(f"tenant isolation failed in {len(report['isolation_failures'])} run(s)")
    bad_inj = [c["id"] for c in report["per_case"] if c["kind"] == "injection" and not c["pass"]]
    if bad_inj:
        reasons.append(f"injection cases failed: {bad_inj}")
    if report["pass_rate"] < min_pass_rate:
        reasons.append(f"pass rate {report['pass_rate']} < {min_pass_rate}")
    if baseline is not None:
        reg = regressions(baseline, report)
        if reg:
            reasons.append(f"regressions vs baseline: {reg}")
    return (not reasons), reasons
