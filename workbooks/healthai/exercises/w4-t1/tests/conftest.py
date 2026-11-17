import json
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from pa_graph.graph import build_graph, start_case
from pa_graph.model import ScriptedChatModel
from pa_graph.review_service import AuditLog, ReviewService
from pa_graph.tools import FakeFhirStore

FIX = Path(__file__).resolve().parent.parent / "fixtures"
DECIDE = {
    "PA-2026-0002": {"decision": "deny", "reviewer": "md-007", "reason": "Criterion 2.b not met: no conservative therapy documented."},
    "PA-2026-0003": {"decision": "approve", "reviewer": "rn-104", "reason": ""},
    "PA-2026-0005": {"decision": "approve", "reviewer": "rn-310", "reason": ""},
    "PA-2026-0006": {"decision": "pend", "reviewer": "rn-221", "reason": "Prior imaging report requested from the provider."},
    "PA-2026-0008": {"decision": "pend", "reviewer": "rn-221", "reason": "Requesting operative notes from the ordering surgeon."},
}


@pytest.fixture
def setup_cases():
    def _make(seed=7, jitter=0.02):
        cases = {c["case_id"]: c for c in json.loads((FIX / "cases.json").read_text())}
        graph = build_graph(ScriptedChatModel.from_file(FIX / "model_responses.json"), FakeFhirStore(FIX / "fhir.json"),
                            checkpointer=InMemorySaver())
        for cid in DECIDE:
            start_case(graph, cases[cid])
        return graph, ReviewService(graph, AuditLog(jitter_s=jitter, seed=seed)), cases
    return _make
