"""Kestrel PA intake graph -- hackathon prototype. Make it production-safe (see README).

What it does today: validate -> fetch_coverage -> assess -> finalize, and finalize copies the
model's outcome straight into the determination. That means the model can deny care on its
own, which the design rule forbids. Keep the public API (build_graph, start_case, resume_case,
config_for, finalize, the node names in README) so the tests and the intake service still work.
"""

from __future__ import annotations

import json
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt  # noqa: F401  (you will need interrupt)

from .model import Recommendation  # noqa: F401  (validate model output with it)
from .state import PAState

APPROVE_THRESHOLD = 0.85
PRIORITIES = {"expedited", "standard"}


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


# TODO: check_completeness node (missing diagnosis code / clinical documentation)
# TODO: request_info node (interrupt with the missing list; resume supplies fields or withdraws)


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
        rec = json.loads(str(msg.content))  # TODO: validate with Recommendation; never crash on bad output
        return {"recommendation": rec, "audit": [{"node": "assess", "outcome": rec.get("outcome")}]}
    return assess


# TODO: routing after assess, human_review node (interrupt), reviewer input validation


STATUS = {"approve": "approved", "deny": "denied", "pend": "pended"}


def make_finalize(threshold: float):
    def finalize(state: PAState) -> dict[str, Any]:
        rec = state.get("recommendation") or {}
        status = STATUS.get(rec.get("outcome", ""), "pended")  # BUG: the model decides
        citations = [c["citation"] for c in rec.get("criteria", []) if c.get("citation")]
        det = {"case_id": state["case_id"], "status": status, "decided_by": "auto",
               "reason": rec.get("rationale", ""), "citations": citations, "priority": state.get("priority")}
        return {"status": status, "determination": det, "audit": [{"node": "finalize", "status": status, "by": "auto"}]}
    return finalize


finalize = make_finalize(APPROVE_THRESHOLD)


def build_graph(model, fhir, checkpointer=None, approve_threshold: float = APPROVE_THRESHOLD):
    g = StateGraph(PAState)
    g.add_node("validate", validate)
    g.add_node("fetch_coverage", make_fetch_coverage(fhir))
    g.add_node("assess", make_assess(model))
    g.add_node("finalize", make_finalize(approve_threshold))
    g.add_edge(START, "validate")
    g.add_conditional_edges("validate", route_after_validate, ["fetch_coverage", END])
    g.add_edge("fetch_coverage", "assess")
    g.add_edge("assess", "finalize")
    g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer)


def start_case(graph, case: dict[str, Any]) -> dict[str, Any]:
    return graph.invoke({**case, "audit": []}, config_for(case["case_id"]))


def resume_case(graph, case_id: str, value: Any) -> dict[str, Any]:
    return graph.invoke(Command(resume=value), config_for(case_id))
