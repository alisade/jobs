"""Reviewer approval tokens for the gated write tool. TODO: README task 3.

token = base64url(canonical_payload, no padding) + "." + hex(HMAC-SHA256(key, canonical_payload))
canonical_payload = JSON of {"eng", "control", "sample", "reviewer", "exp"} with sort_keys=True and
separators=(",", ":"); exp is a Unix timestamp (int seconds).
"""

from __future__ import annotations

from dataclasses import dataclass


class ApprovalError(Exception):
    """The token does not authorize this write. The message says why (signature, expired, scope, malformed)."""


@dataclass(frozen=True)
class Approval:
    engagement: str
    control_id: str
    sample_id: str
    reviewer: str
    expires_at: int


def issue_approval(key: bytes, *, engagement: str, control_id: str, sample_id: str, reviewer: str, expires_at: int) -> str:
    """What the review service does when a human approves (used by the tests and by you to try things)."""
    raise NotImplementedError("TODO: README task 3")


def verify_approval(key: bytes, token: str, *, engagement: str, control_id: str, sample_id: str, now: float) -> Approval:
    """Return the Approval, or raise ApprovalError with a message containing 'malformed', 'signature',
    'expired' or 'scope'. Use a constant-time comparison for the signature."""
    raise NotImplementedError("TODO: README task 3")
