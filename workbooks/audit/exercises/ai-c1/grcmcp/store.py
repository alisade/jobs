"""In-memory stand-in for the MFH GRC system (engagements, control tests, exceptions, evidence).
Complete. The real system is a REST API; the MCP server only ever talks to this interface."""

from __future__ import annotations

import copy
import json
from pathlib import Path

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "grc.json"


class GrcStore:
    def __init__(self, data: dict | None = None):
        self.data = copy.deepcopy(data) if data is not None else json.loads(FIX.read_text())
        self.writes: list[dict] = []

    def engagement(self, eng: str) -> dict:
        if eng not in self.data:
            raise KeyError(eng)
        return self.data[eng]

    def add_exception(self, eng: str, record: dict) -> dict:
        excs = self.data[eng]["exceptions"]
        rec = dict(record, exception_id=f"EXC-{1000 + len(excs)}")
        excs.append(rec)
        self.writes.append({"engagement": eng, **rec})
        return rec
