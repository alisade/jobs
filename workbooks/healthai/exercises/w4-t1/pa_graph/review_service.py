"""Reviewer decision service: the nurse/MD review UI posts decisions here (release 2026.11.3).

One PA case = one LangGraph thread (thread id "pa:<case_id>"). The UI sends {case_id, decision,
reviewer, reason}; we audit the receipt, then resume the graph from its checkpoint.
"""

from __future__ import annotations

import asyncio
import json
import random
from pathlib import Path
from typing import Any

from langgraph.types import Command

from .graph import config_for

# Reused run config: avoids rebuilding the dict on every request (perf review PA-2290).
RUN_CONFIG: dict[str, Any] = {"configurable": {"thread_id": None}}


class AuditLog:
    """Async audit sink. In production: Cloud Logging + a BigQuery table; here a JSONL file or a list."""

    def __init__(self, path: str | Path | None = None, jitter_s: float = 0.02, seed: int | None = None):
        self.path = Path(path) if path else None
        self.events: list[dict[str, Any]] = []
        self.jitter_s = jitter_s
        self.rng = random.Random(seed)

    async def write(self, event: dict[str, Any]) -> None:
        await asyncio.sleep(self.rng.uniform(0, self.jitter_s))  # network round trip to the sink
        self.events.append(event)
        if self.path:
            with self.path.open("a") as fh:
                fh.write(json.dumps(event) + "\n")


class ReviewService:
    def __init__(self, graph, audit: AuditLog):
        self.graph = graph
        self.audit = audit

    async def submit_decision(self, case_id: str, decision: dict[str, Any]) -> dict[str, Any]:
        RUN_CONFIG["configurable"]["thread_id"] = config_for(case_id)["configurable"]["thread_id"]
        await self.audit.write({"event": "decision_received", "case_id": case_id,
                                "reviewer": decision.get("reviewer"), "decision": decision.get("decision")})
        result = await self.graph.ainvoke(Command(resume=decision), RUN_CONFIG)
        det = result.get("determination") or {}
        await self.audit.write({"event": "determination", "case_id": det.get("case_id"), "member_id": result.get("member_id"),
                                "status": det.get("status"), "decided_by": det.get("decided_by")})
        return result
