"""Output contract for enriched catalog attributes. Reference solution."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TAXONOMY = [
    "tents", "sleeping-bags", "sleeping-pads", "packs", "lighting", "stoves", "cookware",
    "coolers", "hydration", "jackets", "footwear", "camp-furniture", "hammocks", "outdoor-decor",
]

Category = Literal[
    "tents", "sleeping-bags", "sleeping-pads", "packs", "lighting", "stoves", "cookware",
    "coolers", "hydration", "jackets", "footwear", "camp-furniture", "hammocks", "outdoor-decor",
]


class EnrichedAttributes(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=80)
    category: Category
    material: str | None = None
    weight_kg: float | None = Field(None, gt=0)
    capacity_l: float | None = Field(None, gt=0)
    color: str | None = None
    care: str | None = None
    description: str = Field(..., min_length=1, max_length=400)
    confidence: float = Field(..., ge=0, le=1)
