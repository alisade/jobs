"""Server-side case state (in production: the case DB behind the review UI)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Case:
    case_id: str
    member_id: str
    documents: list[str]
    auto_approve_eligible: bool = False          # set by the deterministic rules engine, never by the model
    human_decision: dict[str, Any] | None = None  # set only by the review UI
    draft: dict[str, Any] | None = None
    final: dict[str, Any] | None = None
    audit: list[dict[str, Any]] = field(default_factory=list)


class CaseStore:
    def __init__(self, cases: dict[str, Case], documents: dict[str, str]):
        self.cases = cases
        self.documents = documents

    @classmethod
    def load(cls, fixtures: str | Path) -> "CaseStore":
        fx = Path(fixtures)
        raw = json.loads((fx / "cases.json").read_text())
        return cls({c["case_id"]: Case(**c) for c in raw}, json.loads((fx / "documents.json").read_text()))

    def record_human_decision(self, case_id: str, decision: dict[str, Any]) -> None:
        self.cases[case_id].human_decision = decision
        self.cases[case_id].audit.append({"event": "human_decision", **decision})
