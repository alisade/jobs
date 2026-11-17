"""Per-hook fail policy: the week-2 fail-policy matrix as config. Given; do not change."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HookPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    timeout_s: float = Field(gt=0, le=5)
    # What a timeout, a RiskUnavailable, or any other client failure means for this hook.
    on_failure: Literal["open", "closed"]


class TrustPolicy(BaseModel):
    """Defaults: a cart write is cheap to undo, so a sick risk API must not stop
    shopping (fail open, tight budget); checkout is where money moves next, so it fails
    closed with a larger budget."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    cart: HookPolicy = HookPolicy(timeout_s=0.15, on_failure="open")
    checkout: HookPolicy = HookPolicy(timeout_s=0.40, on_failure="closed")
