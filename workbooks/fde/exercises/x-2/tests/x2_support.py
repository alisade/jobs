"""Helpers for the visible tests: configure the trust logging onto a fresh stream and read
back the JSON lines it wrote."""

from __future__ import annotations

import io
import json
import logging
import re

from trustlog.logging_setup import configure

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PAN = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
BIN_FIELD = re.compile(r'"card_bin":\s*"\d{6,8}"')


def reset_trust_loggers() -> None:
    """Undo any previous configure(): handlers and filters on trust and its children."""
    for name in list(logging.root.manager.loggerDict):
        if name == "trust" or name.startswith("trust."):
            lg = logging.getLogger(name)
            for h in list(lg.handlers):
                lg.removeHandler(h)
            for f in list(lg.filters):
                lg.removeFilter(f)


class Capture:
    def __init__(self) -> None:
        reset_trust_loggers()
        self.stream = io.StringIO()
        self.handler = configure(stream=self.stream)

    def lines(self) -> list[dict]:
        self.handler.flush()
        return [json.loads(line) for line in self.stream.getvalue().splitlines() if line.strip()]

    def raw(self) -> str:
        self.handler.flush()
        return self.stream.getvalue()


def pii_findings(text: str) -> list[str]:
    return [p.pattern for p in (EMAIL, PAN, BIN_FIELD) if p.search(text)]
