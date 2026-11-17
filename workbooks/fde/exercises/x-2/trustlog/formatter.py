"""One JSON object per line; custom (extra=) attributes become top-level fields."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from .redact import STANDARD_ATTRS


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        doc = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for attr, value in vars(record).items():
            if attr not in STANDARD_ATTRS:
                doc[attr] = value
        return json.dumps(doc, default=str)
