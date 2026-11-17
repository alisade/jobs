"""Retrieval eval used in the release checklist: recall@3 at section level.  python -m ingest.eval"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .build_index import ingest, search

ROOT = Path(__file__).resolve().parent.parent


def recall_at_3(rows, questions) -> float:
    hit = 0
    for q in questions:
        top = [r.section_id for r in search(rows, q["question"], q["course"], 3)]
        hit += any(s in top for s in q["relevant"])
    return hit / len(questions)


def main() -> int:
    questions = [json.loads(l) for l in (ROOT / "corpus" / "questions.jsonl").read_text().splitlines() if l.strip()]
    rows = ingest(ROOT / "corpus")
    r = recall_at_3(rows, questions)
    print(f"recall@3 = {r:.3f} over {len(questions)} questions ({len(rows)} rows)")
    return 0 if r >= 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())
