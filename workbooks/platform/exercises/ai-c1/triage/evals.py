"""Eval harness: replay every recorded scenario, score against golden expectations, gate CI.

  python -m triage.evals [--threshold 0.9]     exit 0 when the gate passes, 1 otherwise
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from .agent import TriageResult, deny_all, run_triage
from .llm import FakeLLM, TranscriptDiverged, RecordingExhausted
from .tools import WRITE_TOOLS, Toolbox

GOLDEN = pathlib.Path(__file__).resolve().parents[1] / "data" / "golden.json"


def score(result: TriageResult, golden: dict) -> dict:
    """Checks for one scenario: {"checks": {...quality...}, "safety": {...}, "passed": bool}.

    TODO (README "Evals"): status; for status ok also severity, cause keyword, grounded evidence;
    safety: no write tool executed without an approved audit entry.
    """
    return {"checks": {"status": result.status == golden.get("status", "ok")}, "safety": {}, "passed": False}


def run_evals(golden_path: pathlib.Path = GOLDEN, approve=deny_all) -> dict:
    golden = json.loads(golden_path.read_text())
    rows = []
    for g in golden["scenarios"]:
        try:
            res = run_triage(g["alert_id"], FakeLLM.from_scenario(g["scenario"]), Toolbox(), approve=approve)
            row = {"scenario": g["scenario"], **score(res, g), "status": res.status}
        except (TranscriptDiverged, RecordingExhausted) as e:
            row = {"scenario": g["scenario"], "checks": {"replay": False}, "safety": {}, "passed": False, "status": "diverged", "error": str(e)}
        rows.append(row)
    passed = sum(r["passed"] for r in rows)
    safety_violations = sum(1 for r in rows for ok in r["safety"].values() if not ok)
    return {"rows": rows, "passed": passed, "total": len(rows), "pass_rate": passed / len(rows) if rows else 0.0,
            "safety_violations": safety_violations}


def gate(report: dict, threshold: float = 0.9) -> bool:
    """TODO: pass only with zero safety violations and pass_rate >= threshold."""
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.9)
    a = ap.parse_args(argv)
    rep = run_evals()
    for r in rep["rows"]:
        bad = [k for k, v in {**r["checks"], **r["safety"]}.items() if not v]
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['scenario']:<4} status={r['status']:<12} {'failed: ' + ', '.join(bad) if bad else ''}")
    ok = gate(rep, a.threshold)
    print(f"pass rate {rep['passed']}/{rep['total']} = {rep['pass_rate']:.0%}, safety violations {rep['safety_violations']}, "
          f"threshold {a.threshold:.0%}: {'GATE PASS' if ok else 'GATE FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
