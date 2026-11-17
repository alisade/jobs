"""Quarterly PA metrics for CMS-0057-F impacted lines: on-time vs late decisions per priority.

Usage: python -m clockreport.report data/cases.csv out/pa_metrics.json
"""

from __future__ import annotations

import csv
import json
import logging
import statistics
import sys
from datetime import datetime
from pathlib import Path

from .deadlines import decision_deadline

IMPACTED = {"medicare-advantage", "medicaid-mco", "chip-mco"}


def build(cases_csv: str | Path) -> dict:
    out: dict = {"source": str(cases_csv), "excluded_not_impacted": 0}
    buckets = {"expedited": [], "standard": []}
    late: list[str] = []
    with open(cases_csv, newline="") as fh:
        for row in csv.DictReader(fh):
            if row["lob"] not in IMPACTED:
                out["excluded_not_impacted"] += 1
                continue
            received = datetime.fromisoformat(row["received_at"])
            decided = datetime.fromisoformat(row["decided_at"])
            due = decision_deadline(received, row["priority"], row["plan_tz"], row["case_id"])
            on_time = decided <= due
            hours = (decided - received).total_seconds() / 3600
            buckets[row["priority"]].append((on_time, hours))
            if not on_time:
                late.append(row["case_id"])
    for pri, rows in buckets.items():
        out[pri] = {
            "total": len(rows),
            "on_time": sum(1 for ok, _ in rows if ok),
            "late": sum(1 for ok, _ in rows if not ok),
            "median_hours_to_decision": round(statistics.median(h for _, h in rows), 1) if rows else None,
        }
    out["late_case_ids"] = sorted(late)
    return out


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    src, dst = argv[1], argv[2]
    result = build(src)
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_text(json.dumps(result, indent=2) + "\n")
    logging.getLogger("clockreport.report").info(
        "expedited late=%s/%s standard late=%s/%s", result["expedited"]["late"], result["expedited"]["total"],
        result["standard"]["late"], result["standard"]["total"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
