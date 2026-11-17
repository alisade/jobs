"""Specialist tools over the fake store. The requester comes from the verified session, never
from model-produced arguments."""
from __future__ import annotations

import re

from strands import tool

from .store import Store

TICKET_ID = re.compile(r"^IT-\d{5}$")
CATEGORIES = ("hardware", "software", "network", "access")
TEAMS = ("payments", "claims", "underwriting", "platform")


class ToolInputError(ValueError):
    """Raised with a message the model can act on (what was wrong and what is allowed)."""


def it_tools(store: Store, requester: str) -> list:
    @tool
    def get_ticket(ticket_id: str) -> dict:
        """Get one IT ticket by id (format IT-12345). Returns id, summary, category, status."""
        if not TICKET_ID.match(ticket_id or ""):
            raise ToolInputError(f"ticket_id must look like IT-12345, got {ticket_id!r}")
        t = store.get_ticket(ticket_id)
        if t is None:
            raise ToolInputError(f"no ticket {ticket_id}; ask the user to check the number")
        return {k: t[k] for k in ("id", "summary", "category", "status")}

    @tool
    def create_ticket(summary: str, category: str) -> dict:
        """Open an IT ticket for the signed-in user. summary: 10-200 characters.
        category: one of hardware, software, network, access."""
        summary = (summary or "").strip()
        if not 10 <= len(summary) <= 200:
            raise ToolInputError(f"summary must be 10-200 characters, got {len(summary)}")
        if category not in CATEGORIES:
            raise ToolInputError(f"category must be one of {', '.join(CATEGORIES)}, got {category!r}")
        return {"id": store.create_ticket(summary, category, requester), "status": "open"}

    return [get_ticket, create_ticket]


def review_tools(store: Store, requester: str) -> list:
    @tool
    def list_pending_reviews(team: str) -> dict:
        """List pending access reviews for a team (payments, claims, underwriting, platform)."""
        if team not in TEAMS:
            raise ToolInputError(f"team must be one of {', '.join(TEAMS)}, got {team!r}")
        items = store.pending_reviews(team)
        return {"team": team, "count": len(items),
                "reviews": [{k: r[k] for k in ("id", "user", "entitlement")} for r in items[:20]]}

    @tool
    def delete_review(review_id: str) -> dict:
        """Delete an access review record."""
        return {"deleted": store.delete_review(review_id)}

    return [list_pending_reviews, delete_review]
