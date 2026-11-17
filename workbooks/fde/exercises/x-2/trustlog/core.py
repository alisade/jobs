"""Trust-layer lifecycle lines, logged on the parent ``trust`` logger itself."""

from __future__ import annotations

import logging

logger = logging.getLogger("trust")


def log_started(deployment: str, operator_email: str) -> None:
    logger.info("trust layer started for %s by %s", deployment, operator_email)
