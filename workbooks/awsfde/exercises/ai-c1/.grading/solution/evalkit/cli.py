"""CI entry point (done): python -m evalkit.cli fixtures/candidate.jsonl --baseline fixtures/baseline.jsonl

Writes run/report.json and exits 1 when the gate says no-go, 0 otherwise.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from .harness import evaluate, gate
from .io import load_golden, load_runs

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", type=pathlib.Path)
    ap.add_argument("--baseline", type=pathlib.Path)
    ap.add_argument("--golden", type=pathlib.Path, default=ROOT / "fixtures" / "golden.json")
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "run" / "report.json")
    ap.add_argument("--min-pass-rate", type=float, default=0.9)
    a = ap.parse_args(argv)
    golden = load_golden(a.golden)
    rep = evaluate(golden, load_runs(a.runs))
    base = evaluate(golden, load_runs(a.baseline)) if a.baseline else None
    ok, reasons = gate(rep, base, a.min_pass_rate)
    rep["gate"] = {"go": ok, "reasons": reasons}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rep, indent=1) + "\n")
    print(f"pass_rate={rep['pass_rate']} consistency={rep['consistency']} flaky={rep['flaky']} "
          f"isolation={len(rep['isolation_failures'])} -> {'GO' if ok else 'NO-GO'}")
    for r in reasons:
        print("  - " + r)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
