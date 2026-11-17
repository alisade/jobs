"""Output contract for enriched catalog attributes."""

from __future__ import annotations

from pydantic import BaseModel

TAXONOMY = [
    "tents", "sleeping-bags", "sleeping-pads", "packs", "lighting", "stoves", "cookware",
    "coolers", "hydration", "jackets", "footwear", "camp-furniture", "hammocks", "outdoor-decor",
]


class EnrichedAttributes(BaseModel):
    # TODO: enforce the contract in README.md "Output contract":
    #   title 1-80 chars, category one of TAXONOMY, weight_kg and capacity_l > 0 when present,
    #   description at most 400 chars, confidence between 0 and 1, and no unknown fields.
    title: str
    category: str
    material: str | None = None
    weight_kg: float | None = None
    capacity_l: float | None = None
    color: str | None = None
    care: str | None = None
    description: str
    confidence: float
