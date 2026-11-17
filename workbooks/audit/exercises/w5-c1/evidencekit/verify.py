"""Citation verifier: a conclusion stands only if every citation is real and the cited facts support it."""

from __future__ import annotations

import re
from datetime import datetime

from .chunks import Chunk

APPROVAL = re.compile(r"\bapprov", re.IGNORECASE)
CONCLUSIONS = ("approved_before_deploy", "not_approved_before_deploy", "insufficient_evidence")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


class Resolver:
    """Resolves a citation locator to the exact source text it points at (README task 3)."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks

    def text(self, cit: dict) -> str | None:
        """Paragraph: that paragraph's text. Table row: the row line without the header. Table or CSV
        cell (col given): that cell's value. CSV row: the raw line. None when the locator does not exist."""
        raise NotImplementedError("TODO: README task 3 (Resolver.text)")


def _ts(s) -> datetime | None:
    try:
        d = datetime.fromisoformat(str(s))
    except ValueError:
        return None
    return d if d.tzinfo else None


def verify(claim: dict, resolver: Resolver, change_id: str) -> tuple[str, list[dict], list[str]]:
    """Return (status, valid_citations, reasons). status is a CONCLUSIONS value."""
    raise NotImplementedError("TODO: README task 3 (verify)")
