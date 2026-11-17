"""Deterministic checks: every claimed attribute must be supported by the supplier text.
Reference solution."""

from __future__ import annotations

import re

from .models import EnrichedAttributes

BANNED_CLAIMS = ["eco-friendly", "environmentally friendly", "sustainable", "carbon neutral", "non-toxic"]
CONDITIONAL_CLAIMS = ["waterproof"]  # allowed only if the supplier text says it
MIN_CONFIDENCE = 0.6
TOLERANCE = 0.02  # 2 percent, for rounding after unit conversion

_NUM = r"(\d+(?:[.,]\d+)?)"
_WEIGHT_UNITS = {"kg": 1.0, "kilograms": 1.0, "g": 0.001, "grams": 0.001, "lb": 0.45359237,
                 "lbs": 0.45359237, "pounds": 0.45359237, "oz": 0.028349523125, "ounces": 0.028349523125}
_VOLUME_UNITS = {"l": 1.0, "liter": 1.0, "liters": 1.0, "litre": 1.0, "litres": 1.0, "ml": 0.001,
                 "qt": 0.946352946, "quart": 0.946352946, "quarts": 0.946352946, "gal": 3.785411784}


def _quantities(text: str, units: dict[str, float]) -> list[float]:
    alt = "|".join(sorted((re.escape(u) for u in units), key=len, reverse=True))
    out = []
    for m in re.finditer(_NUM + r"\s*(" + alt + r")\b", text, flags=re.IGNORECASE):
        out.append(float(m.group(1).replace(",", ".")) * units[m.group(2).lower()])
    return out


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(TOLERANCE * b, 0.005)


def _mentions(text: str, phrase: str) -> bool:
    return re.search(r"(?<![a-z])" + re.escape(phrase.lower()) + r"(?![a-z])", text.lower()) is not None


def review_reasons(attrs: EnrichedAttributes, source_text: str) -> list[str]:
    """Reasons this item must go to human review instead of being published (empty list = publish)."""
    reasons: list[str] = []
    for name in ("material", "color"):
        value = getattr(attrs, name)
        if value and not _mentions(source_text, value):
            reasons.append(f"unsupported:{name}")
    if attrs.weight_kg is not None and not any(_close(attrs.weight_kg, q) for q in _quantities(source_text, _WEIGHT_UNITS)):
        reasons.append("unsupported:weight_kg")
    if attrs.capacity_l is not None and not any(_close(attrs.capacity_l, q) for q in _quantities(source_text, _VOLUME_UNITS)):
        reasons.append("unsupported:capacity_l")
    claims_text = f"{attrs.title}\n{attrs.description}\n{attrs.care or ''}"
    for term in BANNED_CLAIMS:
        if _mentions(claims_text, term):
            reasons.append(f"banned_claim:{term}")
    for term in CONDITIONAL_CLAIMS:
        if _mentions(claims_text, term) and not _mentions(source_text, term):
            reasons.append(f"unsupported_claim:{term}")
    if attrs.confidence < MIN_CONFIDENCE:
        reasons.append("low_confidence")
    return reasons
