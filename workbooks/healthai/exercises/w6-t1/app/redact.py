"""Identifier redaction used by the logging filter and the span exporter (given; works as designed)."""

from __future__ import annotations

import re

ROSTER = ["Delphine Arkwright", "Tomasz Vellacourt", "Imani Saltonstall", "Ruairi Fenwick-Obi", "Marisol Quennell"]
MEMBER = re.compile(r"\bM-\d{6}\b")
PHONE = re.compile(r"\(?\b\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b")


def roster_names() -> list[str]:
    parts = set()
    for full in ROSTER:
        parts.add(full)
        parts.update(full.replace("-", " ").split())
    return sorted(parts, key=len, reverse=True)


def redact(text: str) -> str:
    for name in roster_names():
        text = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", "[NAME]", text, flags=re.I)
    text = MEMBER.sub("[MEMBER]", text)
    return PHONE.sub("[PHONE]", text)
