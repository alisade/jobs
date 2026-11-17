"""Run a supplier feed through the enrichment pipeline with recorded model answers.

Usage: run_batch.py <feed.jsonl> <recorded-answers.json> <out_dir>
Writes <out_dir>/published.jsonl and prints the review queue and cost.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from enrich.llm import ScriptedLLM  # noqa: E402
from enrich.pipeline import run_batch, write_jsonl  # noqa: E402
from enrich.store import EnrichmentStore  # noqa: E402


def main() -> None:
    feed, answers, out = sys.argv[1:4]
    items = [json.loads(line) for line in open(feed, encoding="utf8") if line.strip()]
    llm = ScriptedLLM(json.load(open(answers, encoding="utf8")))
    os.makedirs(out, exist_ok=True)
    report = run_batch(items, llm, store=EnrichmentStore(os.path.join(out, "store.json")), cost_cap_usd=1.0)
    write_jsonl(report, os.path.join(out, "published.jsonl"))
    print(f"published {len(report.published)}, review {len(report.review)}, skipped {len(report.skipped)}")
    for r in report.review:
        print(f"  REVIEW {r['supplier_sku']}: {', '.join(r['reasons'])}")
    print(f"model calls {report.llm_calls}, cost ${report.cost_usd:.4f}, budget exhausted: {report.budget_exhausted}")
    print(f"wrote {out}/published.jsonl (run again: unchanged items are not re-sent)")


if __name__ == "__main__":
    main()
