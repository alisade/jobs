"""Output grounding check: block answers that state prices or promotions we cannot back up.

Reference solution. Grounding sources are TRUSTED structured fields only: price_cents of the products
the answer cites, and the active promotions table. Review text (UGC) is never evidence, even though it
is in the tool result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

PRICE = re.compile(r"\$\s?([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?)")
CODE = re.compile(r"\b([A-Z]{3,}[0-9]{2,})\b")
PERCENT = re.compile(r"\b([0-9]{1,3})\s?(?:%|percent)", re.IGNORECASE)
CITED_SKU = re.compile(r"\[(KO-[A-Z0-9-]+)\]")


@dataclass
class GroundingResult:
    grounded: bool
    problems: list[str] = field(default_factory=list)


def _cents(amount: str) -> int:
    return round(float(amount.replace(",", "")) * 100)


def check(answer: str, records: list[dict], promotions: dict[str, dict]) -> GroundingResult:
    """Every price must be the cited product's price (or that price after one of its active
    promotions); every code and percent must be an active promotion that applies to a cited product."""
    by_sku = {r["sku"]: r for r in records if isinstance(r.get("price_cents"), int)}
    cited = [s for s in CITED_SKU.findall(answer)]
    problems: list[str] = []

    unknown = [s for s in cited if s not in by_sku]
    for s in unknown:
        problems.append(f"cites {s}, which is not in the tool results")
    cited = [s for s in cited if s in by_sku]

    promos_for: dict[str, list[dict]] = {s: [] for s in cited}
    for p in promotions.values():
        if not p.get("active", True):
            continue
        for s in p.get("skus", []):
            if s in promos_for:
                promos_for[s].append(p)

    allowed_cents: set[int] = set()
    for s in cited:
        price = by_sku[s]["price_cents"]
        allowed_cents.add(price)
        for p in promos_for[s]:
            allowed_cents.add(round(price * (100 - p["percent_off"]) / 100))
    allowed_codes = {p["code"] for ps in promos_for.values() for p in ps}
    allowed_pcts = {int(p["percent_off"]) for ps in promos_for.values() for p in ps}

    prices = PRICE.findall(answer)
    if prices and not cited:
        problems.append("states a price without citing a product")
    for amount in prices:
        if _cents(amount) not in allowed_cents:
            problems.append(f"price ${amount} does not match a cited product's price or active promotion")
    for code in CODE.findall(answer):
        if code not in allowed_codes:
            problems.append(f"code {code} is not an active promotion for the cited products")
    for pct in PERCENT.findall(answer):
        if int(pct) not in allowed_pcts:
            problems.append(f"{pct}% off is not an active promotion for the cited products")
    return GroundingResult(grounded=not problems, problems=problems)
