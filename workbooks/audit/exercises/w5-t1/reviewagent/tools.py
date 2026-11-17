"""Tools for the evidence-review agent."""

from __future__ import annotations

from pathlib import Path

from .evidence import evidence_files, load_layout, paragraphs
from .store import GrcStore

AGENT_IDENTITY = "svc-controlpilot"


def make_tools(store: GrcStore, evidence_dir: str | Path) -> dict:
    def list_evidence(change_id: str) -> dict:
        """List the evidence documents on file for a change."""
        return {"change_id": change_id, "documents": [f.name for f in evidence_files(evidence_dir, change_id)]}

    def get_evidence(change_id: str, document: str) -> dict:
        """Return the paragraphs (page, paragraph index, text) of one evidence document."""
        for f in evidence_files(evidence_dir, change_id):
            if f.name == document:
                return {"document": document, "paragraphs": paragraphs(load_layout(f))}
        return {"error": f"no document {document} for {change_id}"}

    def close_exception(exception_id: str, comment: str) -> dict:
        """Close an open CM-03 exception in GRC Hub with a comment."""
        store.set_status(exception_id, "closed", AGENT_IDENTITY, comment)
        return {"exception_id": exception_id, "status": "closed"}

    def update_workpaper(change_id: str, result: str) -> dict:
        """Set the workpaper result (pass | exception) for a change."""
        store.set_workpaper(change_id, result, AGENT_IDENTITY)
        return {"change_id": change_id, "result": result}

    return {"list_evidence": list_evidence, "get_evidence": get_evidence,
            "close_exception": close_exception, "update_workpaper": update_workpaper}
