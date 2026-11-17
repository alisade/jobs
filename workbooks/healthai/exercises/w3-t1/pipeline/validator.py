"""Structural validator: warnings never block a case; errors do."""

from __future__ import annotations


def validate(bundle: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    kinds = [e["resource"]["resourceType"] for e in bundle["entry"]]
    for need in ("Patient", "Coverage", "Claim"):
        if need not in kinds:
            errors.append(f"missing {need}")
    for e in bundle["entry"]:
        r = e["resource"]
        if r["resourceType"] == "Coverage" and not all("display" in p for p in r.get("payor", [])):
            warnings.append("Coverage.payor[0].display is empty (payer name not shown on letters)")
        if r["resourceType"] == "Condition" and not r.get("code", {}).get("coding"):
            errors.append("Condition without code")
    return errors, warnings
