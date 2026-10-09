"""The Halyard Risk API contract, as the trust mixin sees it (northwind-trust 1.4.0).

The risk API is called in-path on cart writes and at checkout. It never receives raw
identifiers: the session and the customer travel as salted digests (see ``digest``).
"""

from __future__ import annotations

import hashlib
from enum import StrEnum
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

# A per-deployment salt in production (from the secret store); fixed here for the tests.
DIGEST_SALT = "northwind-trust-v1"

Hook = Literal["add_to_cart", "update_cart_item", "checkout"]
Outcome = Literal["allow", "deny", "review", "fail_open", "fail_closed"]


def digest(value: str) -> str:
    """A stable, salted, non-reversible stand-in for an identifier (16 hex chars)."""
    return hashlib.sha256(f"{DIGEST_SALT}:{value}".encode()).hexdigest()[:16]


class Decision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REVIEW = "review"


class RiskRequest(BaseModel):
    """What the mixin sends. Digests only: no session id, user id, name, or email."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    hook: Hook
    session_digest: str
    user_digest: str
    product_id: str | None = None
    quantity: int | None = None  # units being added (the delta, for an update)
    amount: float | None = None  # checkout: the cart subtotal
    currency: str = "USD"


class RiskDecision(BaseModel):
    decision: Decision
    decision_id: str
    reason_codes: list[str] = Field(default_factory=list)  # internal; never shown to the model


class RiskUnavailable(Exception):
    """The risk API answered with an error or could not be reached."""


class RiskClient(Protocol):
    async def assess(self, request: RiskRequest) -> RiskDecision: ...


class DecisionRecord(BaseModel):
    """One structured decision-log line per assessment. PII-free by construction."""

    model_config = ConfigDict(extra="forbid")

    hook: Hook
    outcome: Outcome
    latency_ms: int = Field(ge=0)
    session_digest: str
    decision_id: str | None = None
    reason_codes: list[str] = Field(default_factory=list)
    error: str | None = None  # the exception class name on a failure, never its message
    policy: str | None = None  # "open" or "closed": the on_failure in force for this hook
