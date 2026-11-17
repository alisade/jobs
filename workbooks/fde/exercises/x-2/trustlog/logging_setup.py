"""Logging for the trust layer: everything under the ``trust`` logger goes, as JSON
lines, to decisions.log (shipped to the SIEM), redacted first.

Called once at process start by the host (and by the tests, with a stream).
"""

from __future__ import annotations

import logging
from typing import IO

from .formatter import JsonFormatter
from .redact import RedactingFilter

TRUST_LOGGER = "trust"


def configure(stream: IO[str] | None = None, path: str | None = None) -> logging.Handler:
    """Attach the decisions.log handler to the ``trust`` logger and return it."""
    handler: logging.Handler = (
        logging.FileHandler(path, encoding="utf-8") if path else logging.StreamHandler(stream)
    )
    handler.setFormatter(JsonFormatter())

    trust = logging.getLogger(TRUST_LOGGER)
    trust.setLevel(logging.INFO)
    trust.propagate = False  # decisions.log only; keep these out of the app's root log
    trust.addFilter(RedactingFilter())  # nothing PII-shaped leaves the trust layer
    trust.addHandler(handler)
    return handler
