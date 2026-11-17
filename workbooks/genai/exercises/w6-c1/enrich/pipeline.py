"""Catalog enrichment batch: supplier feed in, validated attributes or a review queue out.

Prototype. It publishes whatever the model says. Every TODO is part of your task (README.md).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from .checks import review_reasons
from .llm import ScriptedLLM
from .models import TAXONOMY, EnrichedAttributes
from .store import EnrichmentStore


@dataclass
class BatchReport:
    published: list[dict] = field(default_factory=list)   # {"supplier_sku", **attributes}
    review: list[dict] = field(default_factory=list)      # {"supplier_sku", "reasons": [...]}
    skipped: list[str] = field(default_factory=list)      # supplier skus not processed (budget)
    llm_calls: int = 0
    cost_usd: float = 0.0
    budget_exhausted: bool = False


def source_hash(description: str) -> str:
    return hashlib.sha256(description.encode("utf8")).hexdigest()[:16]


def build_prompt(item: dict, feedback: str | None = None) -> str:
    lines = [
        "Extract catalog attributes for this supplier product. Use only facts stated in the text.",
        "Return only a JSON object with keys: title, category, material, weight_kg, capacity_l, color,",
        "care, description, confidence. Use null for anything the text does not state.",
        "category must be one of: " + ", ".join(TAXONOMY),
        f"SUPPLIER_SKU: {item['supplier_sku']}",
        "SUPPLIER_TEXT:",
        item["description"],
    ]
    if feedback:
        lines.append(f"Your previous answer was rejected: {feedback}")
    return "\n".join(lines)


def run_batch(
    items: list[dict],
    llm: ScriptedLLM,
    store: EnrichmentStore | None = None,
    cost_cap_usd: float = 5.0,
) -> BatchReport:
    """TODO: retry once with the validation error, deterministic checks, review queue, idempotency
    via the store (keyed by supplier SKU + source hash), cost cap."""
    report = BatchReport()
    for item in items:
        res = llm.complete(build_prompt(item))
        report.llm_calls += 1
        report.cost_usd += res.cost_usd
        try:
            attrs = EnrichedAttributes(**json.loads(res.text))
        except Exception:  # noqa: BLE001
            report.review.append({"supplier_sku": item["supplier_sku"], "reasons": ["invalid_output"]})
            continue
        reasons = review_reasons(attrs, item["description"])
        if reasons:
            report.review.append({"supplier_sku": item["supplier_sku"], "reasons": reasons})
        else:
            report.published.append({"supplier_sku": item["supplier_sku"], **attrs.model_dump()})
    return report


def write_jsonl(report: BatchReport, path: str) -> None:
    with open(path, "w", encoding="utf8") as f:
        for row in report.published:
            f.write(json.dumps(row, sort_keys=True) + "\n")
