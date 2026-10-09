"""Redaction for log records. Given; reviewed by security in PR #377 and correct.

``RedactingFilter`` rewrites a record in place: the formatted message and every custom
(``extra=``) attribute pass through ``redact_value``. It never drops a record.
"""

from __future__ import annotations

import logging
import re
from typing import Any

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# 13-19 digits, optionally grouped by spaces or dashes: a card number (PAN).
PAN = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
SENSITIVE_KEYS = frozenset({"email", "customer_email", "card_bin", "bin", "pan", "phone"})

# Attributes every LogRecord has; anything else arrived through extra=.
STANDARD_ATTRS = frozenset(vars(logging.LogRecord("x", 0, "x", 0, "x", None, None))) | {
    "message",
    "asctime",
    "taskName",
}


def redact_text(text: str) -> str:
    return PAN.sub("[pan]", EMAIL.sub("[email]", text))


def redact_value(value: Any, key: str | None = None) -> Any:
    if key is not None and key.lower() in SENSITIVE_KEYS:
        return "[redacted]"
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {k: redact_value(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_value(v) for v in value]
    return value


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_text(record.getMessage())
        record.args = None
        for attr in list(vars(record)):
            if attr not in STANDARD_ATTRS:
                setattr(record, attr, redact_value(getattr(record, attr), attr))
        return True
