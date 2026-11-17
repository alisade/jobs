"""Read-only tools over a fake FHIR store (Coverage and Condition resources, synthetic data)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


class FakeFhirStore:
    def __init__(self, path: str | Path = FIXTURES / "fhir.json"):
        data = json.loads(Path(path).read_text())
        self.coverage: dict[str, dict[str, Any]] = data["coverage"]
        self.calls: list[tuple[str, str]] = []

    def get_coverage(self, member_id: str) -> dict[str, Any] | None:
        """Active Coverage for the member, or None. Shape: {status, plan, lob, pa_required: [...]}."""
        self.calls.append(("get_coverage", member_id))
        return self.coverage.get(member_id)
