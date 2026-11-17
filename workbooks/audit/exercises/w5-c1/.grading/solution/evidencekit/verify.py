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
    """Resolves a citation locator to the exact source text it points at."""

    def __init__(self, chunks: list[Chunk]):
        self.para: dict[tuple, str] = {}
        self.rows: dict[tuple, Chunk] = {}
        self.csv: dict[tuple, Chunk] = {}
        for c in chunks:
            loc = c.locator
            if c.kind == "paragraph":
                self.para[(loc["blob"], loc["page"], loc["paragraph"])] = c.text
            elif c.kind == "table_row":
                self.rows[(loc["blob"], loc["page"], loc["table"], loc["row"])] = c
            elif c.kind == "csv_row":
                self.csv[(loc["blob"], loc["row"])] = c

    def text(self, cit: dict) -> str | None:
        blob = cit.get("blob")
        try:
            if blob and blob.endswith(".csv"):
                c = self.csv.get((blob, int(cit["row"])))
                if c is None:
                    return None
                if cit.get("col") is not None:
                    col = int(cit["col"])
                    return c.cells[col] if 0 <= col < len(c.cells) else None
                return c.text.split("\n", 1)[1]
            page = int(cit["page"])
            if cit.get("paragraph") is not None:
                return self.para.get((blob, page, int(cit["paragraph"])))
            if cit.get("table") is not None and cit.get("row") is not None:
                c = self.rows.get((blob, page, int(cit["table"]), int(cit["row"])))
                if c is None:
                    return None
                if cit.get("col") is not None:
                    col = int(cit["col"])
                    return c.cells[col] if 0 <= col < len(c.cells) else None
                return c.text.split("\n")[-1]
        except (KeyError, TypeError, ValueError):
            return None
        return None


def _ts(s) -> datetime | None:
    try:
        d = datetime.fromisoformat(str(s))
    except ValueError:
        return None
    return d if d.tzinfo else None


def verify(claim: dict, resolver: Resolver, change_id: str) -> tuple[str, list[dict], list[str]]:
    """Return (status, valid_citations, reasons). status is a CONCLUSIONS value."""
    concl = claim.get("conclusion")
    if concl not in CONCLUSIONS:
        return "insufficient_evidence", [], [f"unknown conclusion {concl!r}"]
    if concl == "insufficient_evidence":
        return "insufficient_evidence", [], ["model reported insufficient evidence"]
    reasons: list[str] = []
    valid: list[dict] = []
    sources: list[tuple[dict, str]] = []
    cits = claim.get("citations") or []
    if not cits:
        reasons.append("no citations")
    for n, cit in enumerate(cits, start=1):
        src = resolver.text(cit)
        if src is None:
            reasons.append(f"citation {n}: locator not found {cit}")
            continue
        if not norm(cit.get("quote")) or norm(cit.get("quote")) not in norm(src):
            reasons.append(f"citation {n}: quote not found at {cit.get('blob')}")
            continue
        valid.append(cit)
        sources.append((cit, src))

    def unit(cit: dict) -> tuple:
        # the unit a fact belongs to: a table row, a CSV row, or a whole document of paragraphs
        if cit.get("table") is not None:
            return (cit.get("blob"), cit.get("page"), cit.get("table"), cit.get("row"))
        if str(cit.get("blob", "")).endswith(".csv"):
            return (cit.get("blob"), cit.get("row"))
        return (cit.get("blob"),)

    def unit_text(cit: dict, src: str) -> str:
        if cit.get("col") is None:
            return src
        whole = {k: v for k, v in cit.items() if k != "col"}
        return resolver.text(whole) or src

    def qualifies(c: dict, src: str) -> bool:
        if c.get("role") == "deploy":
            return change_id in unit_text(c, src)
        # an approval needs the change id AND an approval word together: the table row for table
        # citations, the quote itself for document paragraphs (a mention is not an approval)
        text = unit_text(c, src) if c.get("table") is not None or str(c.get("blob", "")).endswith(".csv") else c.get("quote", "")
        return change_id in text and APPROVAL.search(text) is not None

    def supported(role: str) -> list[dict]:
        mine = [(c, s) for c, s in sources if c.get("role") == role]
        units = {unit(c) for c, s in mine if qualifies(c, s)}
        return [c for c, _ in mine if unit(c) in units]

    appr, dep = supported("approval"), supported("deploy")
    if not appr:
        reasons.append(f"no valid approval citation for {change_id}")
    if not dep:
        reasons.append(f"no valid deploy citation for {change_id}")
    a, d = _ts(claim.get("approval_at")), _ts(claim.get("deployed_at"))
    if a is None or d is None:
        reasons.append("approval_at / deployed_at missing or not an aware ISO timestamp")
    else:
        if not any(norm(str(claim["approval_at"])) in norm(c["quote"]) for c in appr):
            reasons.append("approval_at is not in any approval citation")
        if not any(norm(str(claim["deployed_at"])) in norm(c["quote"]) for c in dep):
            reasons.append("deployed_at is not in any deploy citation")
        computed = "approved_before_deploy" if a < d else "not_approved_before_deploy"
        if computed != concl:
            reasons.append(f"conclusion {concl} contradicts the cited timestamps ({computed})")
    if reasons:
        return "insufficient_evidence", valid, reasons
    return concl, valid, []
