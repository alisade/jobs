"""Visible tests: the happy path and the core rule. Hidden tests cover much more (see README)."""

from pa_graph.graph import config_for, resume_case, start_case


def test_confident_approval_with_all_criteria_met_auto_finalizes(graph, cases):
    out = start_case(graph, cases["PA-2026-0001"])
    assert out["status"] == "approved"
    assert out["determination"]["decided_by"] == "auto"
    assert out["determination"]["citations"] == ["KHP-MP-0417 2.a", "KHP-MP-0417 2.b"]


def test_model_denial_stops_at_human_review(graph, cases):
    out = start_case(graph, cases["PA-2026-0002"])
    assert "__interrupt__" in out, "a model denial must pause for a reviewer"
    assert out.get("status") != "denied"
    snap = graph.get_state(config_for("PA-2026-0002"))
    assert snap.next == ("human_review",)


def test_reviewer_decision_finalizes_with_reviewer_recorded(graph, cases):
    start_case(graph, cases["PA-2026-0002"])
    out = resume_case(graph, "PA-2026-0002", {
        "decision": "deny", "reviewer": "rn-104",
        "reason": "No documentation of six weeks of conservative therapy (policy KHP-MP-0417 2.b).",
    })
    assert out["status"] == "denied"
    assert out["determination"]["decided_by"] == "rn-104"
    assert "conservative therapy" in out["determination"]["reason"]


def test_invalid_submission_is_rejected_without_model_call(graph, cases, model):
    out = start_case(graph, cases["PA-2026-0012"])
    assert out["status"] == "rejected"
    assert model.calls == []
