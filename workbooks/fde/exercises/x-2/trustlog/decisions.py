"""Decision logging, moved out of trust/core.py in PR #412 ("split decision logging into
its own module; no behavior change"). One INFO line per risk decision."""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

logger = logging.getLogger("trust.decisions")


class DecisionEvent(BaseModel):
    decision_id: str
    hook: str
    outcome: str
    reason_codes: list[str] = Field(default_factory=list)
    amount: float | None = None
    card_bin: str | None = None  # first 6-8 digits; the fraud team keys on it
    # Kept on the event for the outcome report, never serialized (security review, PR #377).
    customer_email: str = Field(exclude=True)


def log_decision(event: DecisionEvent) -> None:
    logger.info(
        "decision %s hook=%s customer=%s",
        event.outcome,
        event.hook,
        event.customer_email,
        extra={"decision": event.model_dump()},
    )
