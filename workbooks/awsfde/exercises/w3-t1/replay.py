"""Replay the customers' questions through the answer service and write run/ (done).

Usage: python replay.py [outdir]
"""

from __future__ import annotations

import json
import logging
import pathlib
import sys

from ask_service.answer import answer
from kb_sim.kb import KnowledgeBase

ROOT = pathlib.Path(__file__).resolve().parent


def main(out: str = "run") -> int:
    outdir = ROOT / out
    outdir.mkdir(exist_ok=True)
    for f in ("retrieval.log", "kb.log", "answers.jsonl"):
        (outdir / f).unlink(missing_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s",
                        handlers=[logging.FileHandler(outdir / "retrieval.log")], force=True)
    kb = KnowledgeBase(log_path=outdir / "kb.log")
    rows = []
    for i, line in enumerate((ROOT / "evidence" / "questions.jsonl").read_text().splitlines(), start=1):
        q = json.loads(line)
        a = answer(kb, q["tenant_id"], q["question"], request_id=f"req-{i:04d}")
        rows.append({"request_id": f"req-{i:04d}", **a.__dict__})
    (outdir / "answers.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    foreign = [r for r in rows if any(c["tenant_id"] != r["tenant_id"] for c in r["citations"])]
    by_t: dict[str, list] = {}
    for r in rows:
        by_t.setdefault(r["tenant_id"], []).append(r)
    lines = ["tenant              questions  grounded  no_answer  foreign_citations"]
    for t, rs in sorted(by_t.items()):
        lines.append(f"{t:20}{len(rs):>9}{sum(r['grounded'] for r in rs):>10}"
                     f"{sum(not r['grounded'] for r in rs):>11}"
                     f"{sum(any(c['tenant_id'] != t for c in r['citations']) for r in rs):>19}")
    lines.append(f"retrieve calls: {len(kb.calls)} for {len(rows)} questions")
    lines.append(f"answers citing another tenant: {len(foreign)}")
    (outdir / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
