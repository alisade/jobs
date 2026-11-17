"""Catalog enrichment batch: supplier feed in, validated attributes or a review queue out.
Reference solution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from pydantic import ValidationError

from .checks import review_reasons
from .llm import ScriptedLLM
from .models import TAXONOMY, EnrichedAttributes
from .store import EnrichmentStore

MAX_ATTEMPTS = 2  # first try plus one retry with the error fed back


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


def _parse(text: str) -> EnrichedAttributes:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"not valid JSON ({e.msg} at position {e.pos})") from e
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object")
    return EnrichedAttributes.model_validate(data)


def _error_text(e: Exception) -> str:
    if isinstance(e, ValidationError):
        parts = [f"{'.'.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()]
        return "; ".join(parts)
    return str(e)


def run_batch(
    items: list[dict],
    llm: ScriptedLLM,
    store: EnrichmentStore | None = None,
    cost_cap_usd: float = 5.0,
) -> BatchReport:
    report = BatchReport()
    store = store or EnrichmentStore()
    for idx, item in enumerate(items):
        sku = item["supplier_sku"]
        h = source_hash(item["description"])
        prior = store.get(sku)
        if prior and prior.get("source_hash") == h:
            _record(report, sku, prior)
            continue
        attrs: EnrichedAttributes | None = None
        feedback: str | None = None
        out_of_budget = False
        for _ in range(MAX_ATTEMPTS):
            if report.cost_usd >= cost_cap_usd:
                out_of_budget = True
                break
            res = llm.complete(build_prompt(item, feedback))
            report.llm_calls += 1
            report.cost_usd += res.cost_usd
            try:
                attrs = _parse(res.text)
                break
            except (ValueError, ValidationError) as e:
                feedback = _error_text(e) + ". Return only the JSON object, fixed."
        if out_of_budget and attrs is None:
            report.budget_exhausted = True
            report.skipped.extend(i["supplier_sku"] for i in items[idx:])
            break
        if attrs is None:
            rec = {"source_hash": h, "status": "review", "attributes": None, "reasons": ["invalid_output"]}
        else:
            reasons = review_reasons(attrs, item["description"])
            rec = {
                "source_hash": h,
                "status": "review" if reasons else "published",
                "attributes": attrs.model_dump(),
                "reasons": reasons,
            }
        store.put(sku, rec)
        _record(report, sku, rec)
    report.cost_usd = round(report.cost_usd, 6)
    return report


def _record(report: BatchReport, sku: str, rec: dict) -> None:
    if rec["status"] == "published":
        report.published.append({"supplier_sku": sku, **rec["attributes"]})
    else:
        report.review.append({"supplier_sku": sku, "reasons": list(rec["reasons"])})


def write_jsonl(report: BatchReport, path: str) -> None:
    with open(path, "w", encoding="utf8") as f:
        for row in report.published:
            f.write(json.dumps(row, sort_keys=True) + "\n")
