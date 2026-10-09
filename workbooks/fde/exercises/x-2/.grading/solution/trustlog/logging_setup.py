"""Logging for the trust layer: everything under the ``trust`` logger goes, as JSON
lines, to decisions.log (shipped to the SIEM), redacted first.

Fixed: the RedactingFilter is attached to the HANDLER. A filter on a logger runs only for
records created on that exact logger; a record from ``trust.decisions`` propagates to the
``trust`` logger's handlers without passing the ``trust`` logger's filters. Handler
filters run for every record the handler emits, whatever logger it came from.
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
    handler.addFilter(RedactingFilter())  # runs for trust.* records at any depth

    trust = logging.getLogger(TRUST_LOGGER)
    trust.setLevel(logging.INFO)
    trust.propagate = False  # decisions.log only; keep these out of the app's root log
    trust.addHandler(handler)
    return handler
