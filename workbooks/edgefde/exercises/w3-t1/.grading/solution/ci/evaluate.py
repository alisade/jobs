"""CI step 3/4: evaluate a registered version on the pinned holdout and log the metrics.

    python -m ci.evaluate --data data --model pump-anomaly --version 7
"""

from __future__ import annotations

import argparse
import hashlib
import pickle
import sys
from pathlib import Path

import numpy as np

from mlreg.registry import FileRegistry


def metrics(model, table) -> dict[str, float]:
    y = np.asarray(table["y"])
    p = model.predict(table)
    return {"recall": float((p[y == 1] == 1).mean()), "false_alarm_rate": float((p[y == 0] == 1).mean())}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ci.evaluate")
    ap.add_argument("--data", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--version", required=True, type=int)
    args = ap.parse_args(argv)
    data = Path(args.data)
    reg = FileRegistry(data / "registry")
    holdout = data / "holdout.npz"
    sha = hashlib.sha256(holdout.read_bytes()).hexdigest()
    try:
        rec = reg.get_version(args.model, args.version)
        model = pickle.loads(Path(rec["artifact"]).read_bytes())
        m = metrics(model, dict(np.load(holdout)))
    except Exception as exc:
        # An unevaluated model must never reach the gate: fail the build, loudly.
        print(f"ERROR evaluate: evaluation of v{args.version} failed: {exc!r}", file=sys.stderr)
        return 1
    reg.log_metrics(args.model, args.version, sha, m)
    print(f"evaluate: v{args.version} on holdout {sha[:12]}: recall={m['recall']:.4f} false_alarm_rate={m['false_alarm_rate']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
