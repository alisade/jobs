"""Redaction for anything that leaves the server."""

from __future__ import annotations

import hashlib

DIGEST_SALT = "northwind-trust-v1"


def digest(value: str) -> str:
    """Salted, truncated sha256: the same digest the decision logs carry. Given."""
    return hashlib.sha256(f"{DIGEST_SALT}:{value}".encode()).hexdigest()[:16]


def redact_text(text: str, max_chars: int = 500) -> str:
    """Free text (analyst notes) made safe to return: emails -> [email], raw session ids
    (sess-...) -> [session], IPv4 addresses -> [ip], card numbers (13-19 digits, spaces or
    dashes allowed) -> [card], phone numbers -> [phone]; then capped at ``max_chars``.
    Decision ids such as hx-1006-000117 are not PII and must survive intact."""
    # TODO
    raise NotImplementedError("redact_text")
