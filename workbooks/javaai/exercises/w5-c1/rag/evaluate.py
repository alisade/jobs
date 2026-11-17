"""Retrieval eval and CI gate.

    python -m rag.evaluate            # report both strategies, gate the heading strategy vs baseline.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .chunking import Chunk, fixed_chunks, heading_chunks
from .corpus import load_lessons, load_questions
from .metrics import dedupe, reciprocal_rank, recall_at_k
from .retrieve import Index

ROOT = Path(__file__).resolve().parent.parent
# search more chunks than k so that duplicates of one section do not crowd others out
FETCH = 20


def build(strategy: str) -> Index:
    lessons = load_lessons()
    fn = {"fixed": fixed_chunks, "heading": heading_chunks}[strategy]
    chunks: list[Chunk] = [c for l in lessons for c in fn(l)]
    return Index(chunks)


def evaluate(index: Index, questions: list[dict], ks: tuple[int, ...] = (1, 3, 5)) -> dict:
    """Return {"n": .., "recall@1": .., "recall@3": .., "recall@5": .., "mrr": ..}: means over the
    questions, rounded to 4 places.

    TODO(w5-c1): search FETCH chunks per question within its course, map to section ids, dedupe,
    then score.
    """
    return {"n": len(questions), **{f"recall@{k}": 0.0 for k in ks}, "mrr": 0.0}


def gate(report: dict, baseline: dict, tolerance: float = 0.02) -> tuple[bool, list[str]]:
    """Fail when any metric in the baseline (other than n) is more than `tolerance` below it.
    Returns (ok, reasons). A metric missing from the report is a failure.

    TODO(w5-c1)
    """
    return True, []


def main() -> int:
    questions = load_questions()
    reports = {s: evaluate(build(s), questions) for s in ("fixed", "heading")}
    for s, r in reports.items():
        print(f"{s:8} {json.dumps(r)}")
    baseline = json.loads((ROOT / "baseline.json").read_text())
    ok, reasons = gate(reports["heading"], baseline)
    print("GATE " + ("PASS" if ok else "FAIL: " + "; ".join(reasons)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
