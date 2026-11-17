"""Deterministic checks: every claimed attribute must be supported by the supplier text."""

from __future__ import annotations

from .models import EnrichedAttributes

BANNED_CLAIMS = ["eco-friendly", "environmentally friendly", "sustainable", "carbon neutral", "non-toxic"]
CONDITIONAL_CLAIMS = ["waterproof"]  # allowed only if the supplier text says it
MIN_CONFIDENCE = 0.6


def review_reasons(attrs: EnrichedAttributes, source_text: str) -> list[str]:
    """Reasons this item must go to human review instead of being published (empty list = publish).

    TODO (README "Checks"): unsupported material / color / weight_kg / capacity_l (with unit
    conversion), banned claims, conditional claims, low confidence.
    """
    return []
