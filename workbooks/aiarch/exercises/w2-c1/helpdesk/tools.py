"""Specialist tools over the fake store. The requester comes from the verified session, never
from model-produced arguments.

TODO: validate inputs and raise ToolInputError with a message the model can act on (what was
wrong, what is allowed). Keep outputs small: only the fields the README lists.
"""
from __future__ import annotations

from strands import tool

from .store import Store

CATEGORIES = ("hardware", "software", "network", "access")
TEAMS = ("payments", "claims", "underwriting", "platform")


class ToolInputError(ValueError):
    """Raised with a message the model can act on."""


def it_tools(store: Store, requester: str) -> list:
    @tool
    def get_ticket(ticket_id: str) -> dict:
        """Get a ticket."""
        return store.get_ticket(ticket_id)  # TODO: validate id format, handle not found, trim fields

    @tool
    def create_ticket(summary: str, category: str) -> dict:
        """Create a ticket."""
        return {"id": store.create_ticket(summary, category, requester)}  # TODO: validate

    return [get_ticket, create_ticket]


def review_tools(store: Store, requester: str) -> list:
    @tool
    def list_pending_reviews(team: str) -> dict:
        """List reviews."""
        return {"reviews": store.pending_reviews(team)}  # TODO: validate team, trim fields, count

    @tool
    def delete_review(review_id: str) -> dict:
        """Delete an access review record."""
        return {"deleted": store.delete_review(review_id)}

    return [list_pending_reviews, delete_review]
