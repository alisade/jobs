"""A fake JSON store standing in for the ServiceDesk and access-review APIs (works as shipped)."""
from __future__ import annotations

import copy
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


class Store:
    def __init__(self, data_dir: Path = DATA):
        self.tickets = json.loads((data_dir / "tickets.json").read_text())
        self.reviews = json.loads((data_dir / "reviews.json").read_text())
        self._next = 40000 + len(self.tickets)

    def get_ticket(self, ticket_id: str) -> dict | None:
        t = self.tickets.get(ticket_id)
        return copy.deepcopy(t) if t else None

    def create_ticket(self, summary: str, category: str, requester: str) -> str:
        self._next += 1
        tid = f"IT-{self._next}"
        self.tickets[tid] = {"id": tid, "summary": summary, "category": category,
                             "requester": requester, "status": "open"}
        return tid

    def pending_reviews(self, team: str) -> list[dict]:
        return [copy.deepcopy(r) for r in self.reviews if r["team"] == team and r["status"] == "pending"]

    def delete_review(self, review_id: str) -> bool:
        before = len(self.reviews)
        self.reviews = [r for r in self.reviews if r["id"] != review_id]
        return len(self.reviews) != before
