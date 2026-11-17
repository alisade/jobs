"""python -m evalkit.cli --labels data/labels.jsonl --runs data/runs.jsonl --out out/  (complete)

Writes out/report.json and out/summary.md; exits 1 when the regression gate fails."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .data import load_json, load_labels, load_runs
from .report import build_report, gate, to_markdown


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default="data/labels.jsonl")
    ap.add_argument("--runs", default="data/runs.jsonl")
    ap.add_argument("--prices", default="data/prices.json")
    ap.add_argument("--baseline", default="baseline.json")
    ap.add_argument("--out", default="out")
    ap.add_argument("--expected-runs", type=int, default=5)
    a = ap.parse_args(argv)

    report = build_report(load_labels(a.labels), load_runs(a.runs), load_json(a.prices), expected_runs=a.expected_runs)
    base = load_json(a.baseline)
    failures = gate(report, base["metrics"], base["thresholds"])
    report["gate"] = {"passed": not failures, "failures": failures}

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (out / "summary.md").write_text(to_markdown(report))
    print((out / "summary.md").read_text())
    if failures:
        print("GATE FAILED:\n  " + "\n  ".join(failures), file=sys.stderr)
        return 1
    print("gate passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
