"""Tools the model can call. Every tool returns a dict; errors are {"is_error": True, "error": ...}."""

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
        return {"document_id": document_id, "content": self.store.documents[document_id]}

    def tool_draft_determination(self, case_id: str, outcome: str, rationale: str) -> dict[str, Any]:
        c = self.store.cases[case_id]
        c.draft = {"outcome": outcome, "rationale": rationale}
        c.audit.append({"event": "draft", "outcome": outcome})
        return {"ok": True}

    def tool_finalize_determination(self, case_id: str, outcome: str, reviewed: bool = False) -> dict[str, Any]:
        c = self.store.cases[case_id]
        if outcome != "approve" and not reviewed:
            return {"is_error": True, "error": "a denial or pend needs reviewer sign-off (reviewed=true)"}
        c.final = {"outcome": outcome, "by": "agent"}
        c.audit.append({"event": "finalized", "outcome": outcome, "by": "agent", "reviewed_arg": reviewed})
        return {"ok": True, "status": f"{outcome} finalized"}
