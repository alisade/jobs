"""Migrate the golden set to the current schema (v2 adds control_id) WITHOUT touching labels.

Usage: python scripts/refresh_golden.py [--golden labels/golden.jsonl] [--from labels/human_v1/cm03-golden-v1.jsonl]

Labels, overall outcome and provenance (labeled_by, labeled_at) are copied from the existing human
labels; only schema fields are added. Model output is never a source: rows that are not
human-labeled are refused, and the script exits non-zero without writing anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUMAN_PREFIX = "human:"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", default=str(ROOT / "labels" / "golden.jsonl"))
    ap.add_argument("--from", dest="src", default=None, help="human label file to migrate (default: the golden file itself)")
    ap.add_argument("--control-id", default="CM-03")
    a = ap.parse_args()
    src = Path(a.src or a.golden)
    rows = [json.loads(x) for x in src.read_text().splitlines() if x.strip()]
    bad = [r.get("sample_id", "?") for r in rows if not str(r.get("labeled_by", "")).startswith(HUMAN_PREFIX)]
    if bad:
        print(f"refresh-golden: refusing: {len(bad)} rows in {src} are not human-labeled ({', '.join(bad[:5])}). "
              "Restore labels/human_v1 and migrate from it.", file=sys.stderr)
        return 2
    out = []
    for r in rows:
        r = dict(r)
        r.setdefault("control_id", a.control_id)
        r["label_set"] = "cm03-golden-v2"
        out.append(r)
    Path(a.golden).write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in out))
    print(f"refresh-golden: migrated {len(out)} human-labeled rows in {a.golden} (labels unchanged)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
