"""python -m harness.cli --golden labels/golden.jsonl --runs runs/2026Q3/production.jsonl [--json out.json]"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .golden import load_golden, load_runs
from .score import cost_per_100, score


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default="labels/golden.jsonl")
    ap.add_argument("--runs", default="runs/2026Q3/production.jsonl")
    ap.add_argument("--prices", default="config/prices.json")
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)
    golden = load_golden(a.golden)
    runs = load_runs(a.runs)
    s = score(golden, runs)
    s["cost_per_100_samples_usd"] = round(cost_per_100(runs, json.loads(Path(a.prices).read_text())), 4)
    print("ControlPilot eval dashboard - CM-03")
    print(f"  golden set     {a.golden} ({len(golden)} rows)")
    print(f"  runs           {a.runs} ({s['samples']} scored)")
    print(f"  accuracy       {100 * s['accuracy']:.1f}%" if s["accuracy"] is not None else "  accuracy       n/a")
    print(f"  exc. recall    {100 * s['exception_recall']:.1f}% of {s['exceptions_in_golden']}" if s["exception_recall"] is not None else "  exc. recall    n/a")
    print(f"  missed         {', '.join(s['missed_exceptions']) or 'none'}")
    print(f"  cost/100       ${s['cost_per_100_samples_usd']}")
    if a.json:
        Path(a.json).write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
