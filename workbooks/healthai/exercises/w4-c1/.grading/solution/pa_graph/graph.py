"""Kestrel PA intake graph: validate, coverage, completeness, assess, human review, finalize.

Design rule: the model may only recommend. The graph auto-finalizes nothing except a
high-confidence approval with every criterion met and cited. Every denial, every pend, every
low-confidence or unparseable recommendation and every eligibility problem stops at a
LangGraph interrupt for a human reviewer, and finalize() refuses to deny without one.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from pydantic import ValidationError

from .model import Recommendation
from .state import PAState

APPROVE_THRESHOLD = 0.85
PRIORITIES = {"expedited", "standard"}
DECISIONS = {"approve", "deny", "pend"}
MIN_REASON = 15


def config_for(case_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": f"pa:{case_id}"}}


def validate(state: PAState) -> dict[str, Any]:
    errors = []
    for field in ("case_id", "member_id", "service"):
        if not str(state.get(field) or "").strip():
            errors.append(f"{field} is required")
    if state.get("priority") not in PRIORITIES:
        errors.append("priority must be expedited or standard")
    update: dict[str, Any] = {"validation_errors": errors, "audit": [{"node": "validate", "errors": len(errors)}]}
    if errors:
        update["status"] = "rejected"
        update["determination"] = {"case_id": state.get("case_id", ""), "status": "rejected", "errors": errors,
                                   "decided_by": "intake-validation"}
    return update


def route_after_validate(state: PAState) -> str:
    return END if state.get("validation_errors") else "fetch_coverage"


def make_fetch_coverage(fhir):
    def fetch_coverage(state: PAState) -> dict[str, Any]:
        cov = fhir.get_coverage(state["member_id"]) or {}
        return {"coverage": cov, "audit": [{"node": "fetch_coverage", "found": bool(cov)}]}
    return fetch_coverage


def check_completeness(state: PAState) -> dict[str, Any]:
    missing = []
    if not state.get("diagnosis_codes"):
        missing.append("diagnosis code")
    if not state.get("documents"):
        missing.append("clinical documentation")
    return {"missing_info": missing, "audit": [{"node": "check_completeness", "missing": missing}]}


def coverage_active(state: PAState) -> bool:
    return (state.get("coverage") or {}).get("status") == "active"


def route_after_completeness(state: PAState) -> str:
    if not coverage_active(state):
        return "human_review"  # eligibility problems are potential denials: a person decides
    if state.get("missing_info"):
        return "request_info"
    return "assess"


def request_info(state: PAState) -> dict[str, Any]:
    supplied = interrupt({"type": "missing_info", "case_id": state["case_id"], "missing": state.get("missing_info", [])})
    supplied = supplied if isinstance(supplied, dict) else {}
    update: dict[str, Any] = {"audit": [{"node": "request_info", "supplied": sorted(supplied)}]}
    if supplied.get("withdrawn"):
        update["status"] = "withdrawn"
        update["determination"] = {"case_id": state["case_id"], "status": "withdrawn", "decided_by": "provider"}
        return update
    for field in ("diagnosis_codes", "documents"):
        if supplied.get(field):
            update[field] = list(state.get(field) or []) + list(supplied[field])
    return update


def route_after_request_info(state: PAState) -> str:
    return END if state.get("status") == "withdrawn" else "check_completeness"


def build_prompt(state: PAState) -> str:
    return "\n".join([
        "You assess a prior authorization request against medical policy. Recommend only.",
        f"CASE: {state['case_id']}",
        f"PRIORITY: {state['priority']}",
        f"SERVICE: {state['service']}",
        f"DIAGNOSES: {', '.join(state.get('diagnosis_codes') or [])}",
        f"DOCUMENTS: {', '.join(state.get('documents') or [])}",
        "Return JSON matching the Recommendation schema.",
    ])


def make_assess(model):
    def assess(state: PAState) -> dict[str, Any]:
        msg = model.invoke(build_prompt(state))
        try:
            rec = Recommendation.model_validate_json(str(msg.content))
            return {"recommendation": rec.model_dump(), "model_error": "",
                    "audit": [{"node": "assess", "outcome": rec.outcome, "confidence": rec.confidence}]}
        except ValidationError as exc:
            return {"recommendation": {}, "model_error": f"invalid model output: {exc.error_count()} error(s)",
                    "audit": [{"node": "assess", "outcome": "invalid"}]}
    return assess


def auto_approvable(state: PAState, threshold: float) -> bool:
    rec = state.get("recommendation") or {}
    if not rec or state.get("model_error") or not coverage_active(state) or state.get("missing_info"):
        return False
    criteria = rec.get("criteria") or []
    return (rec.get("outcome") == "approve" and float(rec.get("confidence", 0)) >= threshold
            and bool(criteria) and all(c.get("met") and c.get("citation") for c in criteria))


def review_reason(state: PAState, threshold: float) -> str:
    if not coverage_active(state):
        return "coverage not active"
    if state.get("model_error"):
        return "model output invalid"
    rec = state.get("recommendation") or {}
    if rec.get("outcome") != "approve":
        return f"model recommends {rec.get('outcome')}"
    if float(rec.get("confidence", 0)) < threshold:
        return "low confidence"
    return "criterion not met"


def make_route_after_assess(threshold: float):
    def route_after_assess(state: PAState) -> str:
        return "finalize" if auto_approvable(state, threshold) else "human_review"
    return route_after_assess


def validate_decision(value: Any) -> str:
    if not isinstance(value, dict):
        return "decision must be an object"
    if value.get("decision") not in DECISIONS:
        return "decision must be approve, deny or pend"
    if not str(value.get("reviewer") or "").strip():
        return "reviewer is required"
    if value["decision"] in ("deny", "pend") and len(str(value.get("reason") or "").strip()) < MIN_REASON:
        return "a specific reason is required for deny and pend"
    return ""


def make_human_review(threshold: float):
    def human_review(state: PAState) -> dict[str, Any]:
        value = interrupt({
            "type": "review",
            "case_id": state["case_id"],
            "priority": state.get("priority"),
            "reason_for_review": review_reason(state, threshold),
            "recommendation": state.get("recommendation") or {},
            "model_error": state.get("model_error", ""),
            "review_error": state.get("review_error", ""),
        })
        problem = validate_decision(value)
        if problem:
            return {"review_error": problem, "audit": [{"node": "human_review", "rejected_input": problem}]}
        decision = {"decision": value["decision"], "reason": str(value.get("reason") or ""), "reviewer": value["reviewer"]}
        return {"human_decision": decision, "review_error": "",
                "audit": [{"node": "human_review", "reviewer": decision["reviewer"], "decision": decision["decision"]}]}
    return human_review


def route_after_review(state: PAState) -> str:
    return "human_review" if state.get("review_error") else "finalize"


STATUS = {"approve": "approved", "deny": "denied", "pend": "pended"}


def make_finalize(threshold: float):
    def finalize(state: PAState) -> dict[str, Any]:
        human = state.get("human_decision") or {}
        rec = state.get("recommendation") or {}
        citations = [c["citation"] for c in rec.get("criteria", []) if c.get("citation")]
        if human:
            status, by, reason = STATUS[human["decision"]], human["reviewer"], human.get("reason", "")
        elif auto_approvable(state, threshold):
            status, by, reason = "approved", "auto", rec.get("rationale", "")
        else:
            # Invariant: nothing but a qualifying approval finalizes without a person.
            raise RuntimeError(f"refusing to finalize {state.get('case_id')} without a human decision")
        det = {"case_id": state["case_id"], "status": status, "decided_by": by, "reason": reason,
               "citations": citations, "priority": state.get("priority")}
        return {"status": status, "determination": det, "audit": [{"node": "finalize", "status": status, "by": by}]}
    return finalize


finalize = make_finalize(APPROVE_THRESHOLD)


def build_graph(model, fhir, checkpointer=None, approve_threshold: float = APPROVE_THRESHOLD):
    g = StateGraph(PAState)
    g.add_node("validate", validate)
    g.add_node("fetch_coverage", make_fetch_coverage(fhir))
    g.add_node("check_completeness", check_completeness)
    g.add_node("request_info", request_info)
    g.add_node("assess", make_assess(model))
    g.add_node("human_review", make_human_review(approve_threshold))
    g.add_node("finalize", make_finalize(approve_threshold))
    g.add_edge(START, "validate")
    g.add_conditional_edges("validate", route_after_validate, ["fetch_coverage", END])
    g.add_edge("fetch_coverage", "check_completeness")
    g.add_conditional_edges("check_completeness", route_after_completeness, ["human_review", "request_info", "assess"])
    g.add_conditional_edges("request_info", route_after_request_info, ["check_completeness", END])
    g.add_conditional_edges("assess", make_route_after_assess(approve_threshold), ["finalize", "human_review"])
    g.add_conditional_edges("human_review", route_after_review, ["human_review", "finalize"])
    g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer)


def start_case(graph, case: dict[str, Any]) -> dict[str, Any]:
    return graph.invoke({**case, "audit": []}, config_for(case["case_id"]))


def resume_case(graph, case_id: str, value: Any) -> dict[str, Any]:
    return graph.invoke(Command(resume=value), config_for(case_id))
