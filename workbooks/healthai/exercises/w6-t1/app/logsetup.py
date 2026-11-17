"""Logging for the PA assistant: JSON lines to the log sink and log lines as span events.

The redaction filter is attached to both handlers so nothing leaves unredacted (SEC-311).
"""

from __future__ import annotations

import json
import logging

from .redact import redact
from .tracing import TRACER


class RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(str(record.msg))
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        out = {"level": record.levelname, "logger": record.name, "message": record.getMessage(),
               "case_id": getattr(record, "case_id", None)}
        for k in ("member_name", "reviewer_note"):
            if hasattr(record, k):
                out[k] = getattr(record, k)
        if record.exc_info:
            out["exc"] = self.formatException(record.exc_info)
        return json.dumps(out)


class SpanEventHandler(logging.Handler):
    """Bridge: every log line emitted inside a span becomes a span event (as the OTel log bridge does)."""

    def emit(self, record: logging.LogRecord) -> None:
        span = TRACER.current()
        if span is not None:
            span.events.append({"name": "log", "message": self.format(record)})


def build_logger(stream) -> logging.Logger:
    log = logging.getLogger("khp.pa")
    log.handlers.clear()
    log.propagate = False
    log.setLevel(logging.INFO)
    sink = logging.StreamHandler(stream)
    sink.setFormatter(JsonFormatter())
    bridge = SpanEventHandler()
    bridge.setFormatter(logging.Formatter("%(message)s"))
    for h in (sink, bridge):
        h.addFilter(RedactFilter())
        log.addHandler(h)
    return log
