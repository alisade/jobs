"""The risk API client's logging (the HTTP part is out of scope here)."""

from __future__ import annotations

import logging

logger = logging.getLogger("trust.risk")


def log_risk_failure(customer_email: str, card_number: str, error: str) -> None:
    logger.warning(
        "risk call failed for %s card=%s: %s", customer_email, card_number, error,
        extra={"attempt": 1},
    )
