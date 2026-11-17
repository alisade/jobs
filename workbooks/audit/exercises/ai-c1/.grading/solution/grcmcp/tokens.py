"""Reviewer approval tokens for the gated write tool.

token = base64url(canonical_payload, no padding) + "." + hex(HMAC-SHA256(key, canonical_payload))
canonical_payload = JSON of {"eng", "control", "sample", "reviewer", "exp"} with sort_keys=True and
separators=(",", ":"); exp is a Unix timestamp (int seconds).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
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


def _canonical(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


def issue_approval(key: bytes, *, engagement: str, control_id: str, sample_id: str, reviewer: str, expires_at: int) -> str:
    body = _canonical({"eng": engagement, "control": control_id, "sample": sample_id, "reviewer": reviewer, "exp": int(expires_at)})
    sig = hmac.new(key, body, hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(body).decode().rstrip("=") + "." + sig


def verify_approval(key: bytes, token: str, *, engagement: str, control_id: str, sample_id: str, now: float) -> Approval:
    try:
        b64, sig = token.split(".")
        body = base64.urlsafe_b64decode(b64 + "=" * (-len(b64) % 4))
        payload = json.loads(body)
    except Exception:
        raise ApprovalError("malformed approval token") from None
    if not hmac.compare_digest(hmac.new(key, body, hashlib.sha256).hexdigest(), sig):
        raise ApprovalError("invalid signature: the approval token was not issued by the review service or was altered")
    try:
        a = Approval(payload["eng"], payload["control"], payload["sample"], payload["reviewer"], int(payload["exp"]))
    except (KeyError, TypeError, ValueError):
        raise ApprovalError("malformed approval token") from None
    if a.expires_at <= now:
        raise ApprovalError("approval token expired; ask the reviewer for a new approval")
    if (a.engagement, a.control_id, a.sample_id) != (engagement, control_id, sample_id):
        raise ApprovalError(f"approval token scope is {a.engagement}/{a.control_id}/{a.sample_id}, "
                            f"not {engagement}/{control_id}/{sample_id}")
    return a
