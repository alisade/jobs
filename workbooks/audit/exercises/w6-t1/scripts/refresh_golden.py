"""Refresh the golden set to the current schema (v2 adds control_id).

Usage: python scripts/refresh_golden.py [--source runs/replay-2026-10-30.jsonl] [--out labels/golden.jsonl]

Rebuilds every golden row in the v2 shape from the latest replay of the sample, so the golden set
always matches what the agent currently produces field for field.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=str(ROOT / "runs" / "replay-2026-10-30.jsonl"))
    ap.add_argument("--out", default=str(ROOT / "labels" / "golden.jsonl"))
    a = ap.parse_args()
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for line in Path(a.source).read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rows.append({
            "sample_id": r["sample_id"], "change_id": r["change_id"], "control_id": "CM-03",
            "labels": r["outputs"], "overall": r["overall"],
            "labeled_by": "model:" + r.get("model", "unknown"), "labeled_at": now,
            "label_set": "cm03-golden-v2", "notes": "",
        })
    Path(a.out).write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rows))
    print(f"refresh-golden: wrote {len(rows)} rows to {a.out} from {a.source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
