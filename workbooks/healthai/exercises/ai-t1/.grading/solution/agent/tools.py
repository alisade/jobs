"""Tools the model can call. Every tool returns a dict; errors are {"is_error": True, "error": ...}.

Authorization never comes from model-controlled input (tool arguments, document text): finalize checks
server-side case state only.
"""

from __future__ import annotations

from typing import Any

from .store import CaseStore


class Tools:
    def __init__(self, store: CaseStore):
        self.store = store

    def call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        fn = getattr(self, f"tool_{name}", None)
        if fn is None:
            return {"is_error": True, "error": f"unknown tool {name}"}
        return fn(**args)

    def tool_get_case(self, case_id: str) -> dict[str, Any]:
        c = self.store.cases[case_id]
        return {"case_id": c.case_id, "documents": c.documents, "has_human_decision": c.human_decision is not None}

    def tool_get_document(self, document_id: str) -> dict[str, Any]:
        # Clinical documents come from providers: untrusted data, never instructions.
        return {"document_id": document_id, "trust": "untrusted", "content": self.store.documents[document_id]}

    def tool_draft_determination(self, case_id: str, outcome: str, rationale: str) -> dict[str, Any]:
        c = self.store.cases[case_id]
        c.draft = {"outcome": outcome, "rationale": rationale}
        c.audit.append({"event": "draft", "outcome": outcome})
        return {"ok": True}

    def tool_finalize_determination(self, case_id: str, outcome: str, reviewed: bool = False) -> dict[str, Any]:
        # `reviewed` is accepted for backward compatibility and ignored: the model controls it.
        c = self.store.cases[case_id]
        human = c.human_decision
        if human is not None:
            if human.get("decision") != outcome:
                c.audit.append({"event": "finalize_refused", "outcome": outcome, "reason": "differs from reviewer"})
                return {"is_error": True, "error": "outcome differs from the reviewer's decision"}
            by = human.get("reviewer", "reviewer")
        elif outcome == "approve" and c.auto_approve_eligible:
            by = "auto"
        else:
            c.audit.append({"event": "finalize_refused", "outcome": outcome, "reason": "no human decision"})
            return {"is_error": True, "error": "only a reviewer can finalize this case; draft it and stop"}
        c.final = {"outcome": outcome, "by": by}
        c.audit.append({"event": "finalized", "outcome": outcome, "by": by})
        return {"ok": True, "status": f"{outcome} finalized"}
