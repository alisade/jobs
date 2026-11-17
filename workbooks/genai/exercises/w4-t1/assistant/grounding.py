"""Output grounding check: block answers that state prices or promotions we cannot back up.

Shipped in 2026.10.20 after the "invented price" incident. Every answer passes through check() before
the customer sees it (see pipeline.py).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

PRICE = re.compile(r"\$\s?([0-9]+(?:\.[0-9]{2})?)")
CODE = re.compile(r"\b([A-Z]{3,}[0-9]{2,})\b")
PERCENT = re.compile(r"\b([0-9]{1,2})\s?(?:%|percent)", re.IGNORECASE)
CITED_SKU = re.compile(r"\[(KO-[A-Z0-9-]+)\]")


@dataclass
class GroundingResult:
    grounded: bool
    problems: list[str] = field(default_factory=list)


def check(answer: str, records: list[dict], promotions: dict[str, dict]) -> GroundingResult:
    """An answer is grounded when every price, promo code and percent it states is backed by the
    tool results the model was given."""
    evidence = json.dumps(records) + " " + json.dumps(promotions)
    problems = []
    for amount in PRICE.findall(answer):
        if amount not in evidence and str(int(float(amount) * 100)) not in evidence:
            problems.append(f"price ${amount} not found in tool results")
    for code in CODE.findall(answer):
        if code not in evidence:
            problems.append(f"code {code} not found in tool results")
    for pct in PERCENT.findall(answer):
        if pct not in evidence:
            problems.append(f"{pct}% not found in tool results")
    return GroundingResult(grounded=not problems, problems=problems)
