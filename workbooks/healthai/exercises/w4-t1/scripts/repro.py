"""Replay the 2026-11-20 10:42 review burst: three reviewers submit decisions at the same moment.

python scripts/repro.py [audit.jsonl]
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from langgraph.checkpoint.memory import InMemorySaver  # noqa: E402

from pa_graph.graph import build_graph, start_case  # noqa: E402
from pa_graph.model import ScriptedChatModel  # noqa: E402
from pa_graph.review_service import AuditLog, ReviewService  # noqa: E402
from pa_graph.tools import FakeFhirStore  # noqa: E402

FIX = ROOT / "fixtures"
DECISIONS = {
    "PA-2026-0002": {"decision": "deny", "reviewer": "md-007", "reason": "Criterion 2.b not met: no conservative therapy documented."},
    "PA-2026-0003": {"decision": "approve", "reviewer": "rn-104", "reason": ""},
    "PA-2026-0008": {"decision": "pend", "reviewer": "rn-221", "reason": "Requesting operative notes from the ordering surgeon."},
}


async def main(audit_path: str | None):
    cases = {c["case_id"]: c for c in json.loads((FIX / "cases.json").read_text())}
    graph = build_graph(ScriptedChatModel.from_file(FIX / "model_responses.json"), FakeFhirStore(FIX / "fhir.json"),
                        checkpointer=InMemorySaver())
    for cid in DECISIONS:
        start_case(graph, cases[cid])  # all three wait at human_review
    if audit_path:
        Path(audit_path).write_text("")
    svc = ReviewService(graph, AuditLog(audit_path, seed=1042))
    results = await asyncio.gather(*(svc.submit_decision(cid, d) for cid, d in DECISIONS.items()), return_exceptions=True)
    for cid, r in zip(DECISIONS, results):
        if isinstance(r, Exception):
            print(f"{cid}: ERROR {r!r}")
            continue
        det = r.get("determination") or {}
        print(f"submitted for {cid} ({cases[cid]['member_id']}) by {DECISIONS[cid]['reviewer']:<7} -> "
              f"determination on {det.get('case_id')} member {r.get('member_id')} status {det.get('status')} by {det.get('decided_by')}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else None))
