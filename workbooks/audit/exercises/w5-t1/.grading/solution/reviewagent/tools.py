"""Tools for the evidence-review agent: read-only. Write actions live in gate.py behind approval."""

from __future__ import annotations

from pathlib import Path

from .evidence import evidence_files, load_layout, paragraphs
from .store import GrcStore

AGENT_IDENTITY = "svc-controlpilot"
READ_ONLY_TOOLS = ("list_evidence", "get_evidence")


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

    return {"list_evidence": list_evidence, "get_evidence": get_evidence}
