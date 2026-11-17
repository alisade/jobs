"""Redaction for anything that leaves the server. Reference solution."""

from __future__ import annotations

import hashlib
import re

DIGEST_SALT = "northwind-trust-v1"


def digest(value: str) -> str:
    """Salted, truncated sha256: the same digest the decision logs carry."""
    return hashlib.sha256(f"{DIGEST_SALT}:{value}".encode()).hexdigest()[:16]


# Order matters: cards before phones (a PAN also looks like a long phone number), and
# decision ids (hx-1006-000117) must survive, hence the guards against a leading word
# character or hyphen.
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_SESSION = re.compile(r"\bsess-[A-Za-z0-9-]+")
_IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
_CARD = re.compile(r"(?<![\w-])(?:\d[ -]?){12,18}\d(?![\w-])")
_PHONE = re.compile(r"(?<![\w-])(?:\+\d{1,3}[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]?\d{3}[ .-]?\d{4}(?![\w-])")

_RULES = ((_EMAIL, "[email]"), (_SESSION, "[session]"), (_IPV4, "[ip]"), (_CARD, "[card]"), (_PHONE, "[phone]"))


def redact_text(text: str, max_chars: int = 500) -> str:
    out = text or ""
    for pattern, replacement in _RULES:
        out = pattern.sub(replacement, out)
    return out[:max_chars]
