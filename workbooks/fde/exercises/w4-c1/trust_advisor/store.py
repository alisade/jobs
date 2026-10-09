"""Read-only decision store over the vendor export (JSONL). Given.

The export is RAW: records carry the session id, customer email, client IP and free-text
analyst notes. Nothing from here may reach a tool result unfiltered.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path(__file__).resolve().parent / "data" / "decisions.jsonl"


class DecisionStore:
    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._records = sorted(records, key=lambda r: r["ts"])
        self._by_id = {r["decision_id"]: r for r in self._records}

    @classmethod
    def from_jsonl(cls, path: str | Path = DEFAULT_PATH) -> DecisionStore:
        lines = Path(path).read_text().splitlines()
        return cls([json.loads(line) for line in lines if line.strip()])

    def get(self, decision_id: str) -> dict[str, Any] | None:
        record = self._by_id.get(decision_id)
        return dict(record) if record is not None else None

    def recent(self, n: int, hook: str | None = None) -> list[dict[str, Any]]:
        """The newest ``n`` records (optionally for one hook), oldest first."""
        rows = [r for r in self._records if hook is None or r["hook"] == hook]
        return [dict(r) for r in rows[-n:]] if n > 0 else []
