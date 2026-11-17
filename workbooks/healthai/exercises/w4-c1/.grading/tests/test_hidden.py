"""Hidden tests for healthai/w4-c1. Fixtures come from tests/conftest.py (copied alongside)."""

import itertools
import json
import sqlite3
from pathlib import Path

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

from pa_graph import graph as G
from pa_graph.model import ScriptedChatModel
from pa_graph.tools import FakeFhirStore

FIX = Path(__file__).resolve().parent.parent / "fixtures"
DENY = {"decision": "deny", "reviewer": "md-007", "reason": "Criterion 2.b not met: no conservative therapy documented."}
PEND = {"decision": "pend", "reviewer": "rn-221", "reason": "Prior imaging report requested from the ordering provider."}
APPROVE = {"decision": "approve", "reviewer": "rn-104", "reason": ""}


def payload(out):
    assert "__interrupt__" in out, f"expected an interrupt, got status={out.get('status')}"
    return out["__interrupt__"][0].value


def nodes(out):
    return [a.get("node") for a in out.get("audit", [])]


@pytest.mark.parametrize("cid", ["PA-2026-0002", "PA-2026-0008"])
def test_every_model_denial_interrupts(graph, cases, cid):
    out = G.start_case(graph, cases[cid])
    p = payload(out)
    assert p["type"] == "review"
    assert out.get("status") not in ("denied", "approved")


def test_low_confidence_approval_goes_to_review(graph, cases):
    p = payload(G.start_case(graph, cases["PA-2026-0003"]))
    assert p["reason_for_review"] == "low confidence"


def test_unparseable_model_output_goes_to_review(graph, cases):
    out = G.start_case(graph, cases["PA-2026-0004"])
    p = payload(out)
    assert p["model_error"], "model_error must explain the bad output"
    assert p["recommendation"] == {}


def test_out_of_range_model_output_goes_to_review(graph, cases):
    p = payload(G.start_case(graph, cases["PA-2026-0009"]))
    assert p["model_error"] and p["recommendation"] == {}


def test_approve_with_unmet_criterion_goes_to_review(graph, cases):
    p = payload(G.start_case(graph, cases["PA-2026-0005"]))
    assert p["reason_for_review"] == "criterion not met"


def test_pend_recommendation_goes_to_review(graph, cases):
    p = payload(G.start_case(graph, cases["PA-2026-0006"]))
    assert p["reason_for_review"] == "model recommends pend"


def test_inactive_coverage_reviewed_without_model_call(graph, cases, model):
    out = G.start_case(graph, cases["PA-2026-0010"])
    p = payload(out)
    assert p["reason_for_review"] == "coverage not active"
    assert "PA-2026-0010" not in model.calls
    assert graph.get_state(G.config_for("PA-2026-0010")).next == ("human_review",)


def test_missing_info_interrupt_then_supply(graph, cases):
    out = G.start_case(graph, cases["PA-2026-0011"])
    p = payload(out)
    assert p["type"] == "missing_info"
    assert set(p["missing"]) == {"diagnosis code", "clinical documentation"}
    assert graph.get_state(G.config_for("PA-2026-0011")).next == ("request_info",)
    out = G.resume_case(graph, "PA-2026-0011", {"diagnosis_codes": ["M54.16"], "documents": ["DOC-11"]})
    p = payload(out)  # no recorded model answer for this case -> invalid output -> review
    assert p["type"] == "review"
    st = graph.get_state(G.config_for("PA-2026-0011")).values
    assert st["diagnosis_codes"] == ["M54.16"] and st["documents"] == ["DOC-11"]


def test_missing_info_withdrawn(graph, cases):
    G.start_case(graph, cases["PA-2026-0011"])
    out = G.resume_case(graph, "PA-2026-0011", {"withdrawn": True})
    assert out["status"] == "withdrawn"
    assert "__interrupt__" not in out


@pytest.mark.parametrize("bad", [
    {"decision": "deny", "reviewer": "md-007", "reason": "no"},
    {"decision": "deny", "reviewer": "", "reason": "Criterion 2.b not met: no conservative therapy documented."},
    {"decision": "maybe", "reviewer": "md-007", "reason": "Criterion 2.b not met: no conservative therapy documented."},
    {"decision": "pend", "reviewer": "rn-1"},
    "deny",
])
def test_invalid_reviewer_input_reinterrupts(graph, cases, bad):
    G.start_case(graph, cases["PA-2026-0002"])
    out = G.resume_case(graph, "PA-2026-0002", bad)
    p = payload(out)
    assert p["type"] == "review" and p["review_error"]
    out = G.resume_case(graph, "PA-2026-0002", DENY)
    assert out["status"] == "denied" and out["determination"]["decided_by"] == "md-007"


def test_reviewer_can_approve_low_confidence_without_reason(graph, cases):
    G.start_case(graph, cases["PA-2026-0003"])
    out = G.resume_case(graph, "PA-2026-0003", APPROVE)
    assert out["status"] == "approved" and out["determination"]["decided_by"] == "rn-104"


def test_review_payload_carries_priority_and_recommendation(graph, cases):
    p = payload(G.start_case(graph, cases["PA-2026-0002"]))
    assert p["priority"] == "expedited"
    assert p["recommendation"]["outcome"] == "deny"
    assert p["case_id"] == "PA-2026-0002"


def _deny_state():
    return {"case_id": "PA-X", "member_id": "M-100201", "priority": "standard", "service": "lumbar-mri",
            "diagnosis_codes": ["M54.16"], "documents": ["D"], "coverage": {"status": "active"}, "missing_info": [],
            "recommendation": {"outcome": "deny", "confidence": 0.99, "rationale": "not necessary at all",
                               "criteria": [{"criterion_id": "C1", "met": False, "citation": "KHP-MP-1 1.a"}]},
            "model_error": "", "audit": []}


def test_finalize_refuses_denial_without_human():
    with pytest.raises(Exception):
        G.finalize(_deny_state())


def test_finalize_refuses_low_confidence_approval_without_human():
    s = _deny_state()
    s["recommendation"] = {"outcome": "approve", "confidence": 0.5, "rationale": "probably fine overall",
                           "criteria": [{"criterion_id": "C1", "met": True, "citation": "KHP-MP-1 1.a"}]}
    with pytest.raises(Exception):
        G.finalize(s)


def test_finalize_uses_human_decision():
    s = _deny_state()
    s["human_decision"] = dict(DENY)
    out = G.finalize(s)
    assert out["status"] == "denied" and out["determination"]["decided_by"] == "md-007"


def test_invariant_no_denial_or_pend_without_a_person(cases):
    """Drive every case with every reviewer answer: nothing adverse is ever decided by 'auto'."""
    for cid, decision in itertools.product(sorted(cases), [DENY, PEND, APPROVE]):
        m = ScriptedChatModel.from_file(FIX / "model_responses.json")
        g = G.build_graph(m, FakeFhirStore(FIX / "fhir.json"), checkpointer=InMemorySaver())
        out = G.start_case(g, cases[cid])
        for _ in range(4):
            if "__interrupt__" not in out:
                break
            p = out["__interrupt__"][0].value
            value = {"diagnosis_codes": ["M54.16"], "documents": ["D"]} if p["type"] == "missing_info" else decision
            out = G.resume_case(g, cid, value)
        status = out.get("status")
        assert status is not None, f"{cid} never finished"
        if status in ("denied", "pended"):
            assert out["determination"]["decided_by"] != "auto", f"{cid}: adverse outcome without a reviewer"
            assert "human_review" in nodes(out), f"{cid}: no human_review in the audit trail"
        if out["determination"].get("decided_by") == "auto":
            assert status in ("approved", "rejected")


def test_resume_after_process_restart_with_sqlite(tmp_path, cases):
    db = tmp_path / "checkpoints.db"
    conn = sqlite3.connect(db, check_same_thread=False)
    g1 = G.build_graph(ScriptedChatModel.from_file(FIX / "model_responses.json"), FakeFhirStore(FIX / "fhir.json"),
                       checkpointer=SqliteSaver(conn))
    payload(G.start_case(g1, cases["PA-2026-0008"]))
    conn.close()
    del g1
    conn2 = sqlite3.connect(db, check_same_thread=False)
    m2 = ScriptedChatModel.from_file(FIX / "model_responses.json")
    g2 = G.build_graph(m2, FakeFhirStore(FIX / "fhir.json"), checkpointer=SqliteSaver(conn2))
    assert g2.get_state(G.config_for("PA-2026-0008")).next == ("human_review",)
    out = G.resume_case(g2, "PA-2026-0008", DENY)
    conn2.close()
    assert out["status"] == "denied"
    assert m2.calls == [], "resuming must not call the model again"
    assert nodes(out)[0] == "validate" and nodes(out)[-1] == "finalize"


def test_threads_do_not_mix(graph, cases):
    G.start_case(graph, cases["PA-2026-0002"])
    G.start_case(graph, cases["PA-2026-0008"])
    b = G.resume_case(graph, "PA-2026-0008", PEND)
    a = G.resume_case(graph, "PA-2026-0002", DENY)
    assert a["determination"]["case_id"] == "PA-2026-0002" and a["determination"]["decided_by"] == "md-007"
    assert b["determination"]["case_id"] == "PA-2026-0008" and b["determination"]["decided_by"] == "rn-221"
    assert a["member_id"] == "M-100202" and b["member_id"] == "M-100204"


def test_audit_trail_order(graph, cases):
    G.start_case(graph, cases["PA-2026-0002"])
    out = G.resume_case(graph, "PA-2026-0002", DENY)
    assert nodes(out) == ["validate", "fetch_coverage", "check_completeness", "assess", "human_review", "finalize"]
    rev = [a for a in out["audit"] if a.get("node") == "human_review"][-1]
    assert rev["reviewer"] == "md-007"


def test_threshold_is_configurable(cases, fhir):
    m = ScriptedChatModel.from_file(FIX / "model_responses.json")
    g = G.build_graph(m, fhir, checkpointer=InMemorySaver(), approve_threshold=0.95)
    p = payload(G.start_case(g, cases["PA-2026-0001"]))  # 0.93 < 0.95
    assert p["reason_for_review"] == "low confidence"
