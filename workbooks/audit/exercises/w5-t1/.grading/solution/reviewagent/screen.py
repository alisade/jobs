"""Deterministic screening of evidence for text aimed at the agent. Flags; never edits evidence."""

from __future__ import annotations

import re

PATTERNS = [
    (r"\b(note|message|instructions?)\s+(to|for)\s+(the\s+)?(audit\s+)?(agent|assistant|ai|model|llm)\b", "addresses the agent"),
    (r"\bignore\s+(all\s+|any\s+)?(previous|prior|above|earlier)\b", "override attempt"),
    (r"\b(system|developer)\s+(note|prompt|message|instruction)\b", "fake system text"),
    (r"\bcall\s+[a-z_]+\b|\b[a-z]+_[a-z_]+\s*\(", "asks for a tool call"),
    (r"\bmark\b.{0,60}\b(as\s+)?(pass(ed)?|approved|effective|resolved)\b", "asks to change a result"),
    (r"\bdo\s+not\s+(mention|disclose|report|tell)\b", "asks to hide itself"),
]


def _hidden(style: dict) -> bool:
    color = str(style.get("color", "")).upper()
    bg = str(style.get("backgroundColor", "")).upper()
    if not color:
        return False
    return color == bg or (not bg and color in ("#FFFFFF", "#FFF"))


def screen_evidence(layout: dict) -> list[dict]:
    flags = []
    hidden_spans = [(s["offset"], s["offset"] + s["length"]) for st in layout.get("styles", []) if _hidden(st) for s in st.get("spans", [])]
    for i, p in enumerate(layout.get("paragraphs", [])):
        page = p["boundingRegions"][0]["pageNumber"]
        text = p["content"]
        for sp in p.get("spans", []):
            a, b = sp["offset"], sp["offset"] + sp["length"]
            if any(x < b and a < y for x, y in hidden_spans):
                flags.append({"kind": "hidden_text", "page": page, "paragraph": i, "text": text[:200]})
                break
        reasons = [why for pat, why in PATTERNS if re.search(pat, text, re.IGNORECASE)]
        if reasons:
            flags.append({"kind": "instruction_like_text", "page": page, "paragraph": i, "reasons": reasons, "text": text[:200]})
    return flags
