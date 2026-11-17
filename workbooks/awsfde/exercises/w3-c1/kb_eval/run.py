"""CLI: evaluate both recorded KB configs, write run/report-*.json and run/compare.json (done)."""

from __future__ import annotations

import json
import pathlib
import sys

from .fake_kb import RecordedKnowledgeBase
from .harness import compare, evaluate, gate

KB_ID = "KBTIDEWATER01"


def main(out: str = "run") -> int:
    root = pathlib.Path(__file__).resolve().parent.parent
    golden = json.loads((root / "fixtures" / "golden.json").read_text())
    outdir = root / out
    outdir.mkdir(exist_ok=True)
    reports = {}
    for cfg in ("fixed", "hierarchical"):
        kb = RecordedKnowledgeBase.from_fixtures(cfg)
        rep = evaluate(kb, KB_ID, golden, k=5, config_name=cfg)
        ok, reasons = gate(rep)
        rep["gate"] = {"go": ok, "reasons": reasons}
        reports[cfg] = rep
        (outdir / f"report-{cfg}.json").write_text(json.dumps(rep, indent=1) + "\n")
        print(f"{cfg:13} recall@5={rep['recall_at_k']:.3f} mrr={rep['mrr']:.3f} leaks={len(rep['leaks'])} "
              f"gate={'GO' if ok else 'NO-GO'} {'; '.join(reasons)}")
    (outdir / "compare.json").write_text(json.dumps(compare(reports["fixed"], reports["hierarchical"]), indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
