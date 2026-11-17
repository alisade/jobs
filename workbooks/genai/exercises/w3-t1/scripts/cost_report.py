"""Summarize a provider usage export (CSV). Extend it to answer your own questions.

Usage: cost_report.py evidence/usage-export.csv
"""

import csv
import sys
from collections import defaultdict


def main(path: str) -> None:
    rows = list(csv.DictReader(open(path, newline="")))
    by_fp: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_fp[r["request_fingerprint"]].append(r)
    total = sum(float(r["billed_usd"]) for r in rows)
    print(f"rows: {len(rows)}  distinct requests: {len(by_fp)}  billed: ${total:.2f}")
    print("top requests by billed cost:")
    top = sorted(by_fp.items(), key=lambda kv: -sum(float(r["billed_usd"]) for r in kv[1]))[:8]
    for fp, rs in top:
        cost = sum(float(r["billed_usd"]) for r in rs)
        models = ",".join(sorted({r["model"] for r in rs}))
        print(f"  {fp}  billed {len(rs)}x  ${cost:.3f}  models={models}  "
              f"output_tokens={rs[0]['output_tokens']}  duration_s={rs[0]['duration_s']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "evidence/usage-export.csv")
