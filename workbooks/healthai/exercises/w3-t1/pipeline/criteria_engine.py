"""Rule-based pre-check that runs before clinical review (not a decision: routes the case)."""

from __future__ import annotations

from . import terminology as T

POLICIES = {
    "oncology-pet": {"policy": "KHP-MP-0610", "dx_prefix": ("C",)},
    "chemo-infusion": {"policy": "KHP-MP-0622", "dx_prefix": ("C", "D0")},
    "cardiac-pet": {"policy": "KHP-MP-0212", "dx_prefix": ("I",)},
    "cardiac-cath": {"policy": "KHP-MP-0215", "dx_prefix": ("I", "R07")},
    "lumbar-mri": {"policy": "KHP-MP-0417", "dx_prefix": ()},
    "knee-arthroscopy": {"policy": "KHP-MP-0388", "dx_prefix": ()},
}


def diagnoses(bundle: dict) -> list[str]:
    out = []
    for e in bundle["entry"]:
        r = e["resource"]
        if r["resourceType"] == "Condition":
            out += [c["code"] for c in r["code"]["coding"] if c.get("system") == T.ICD10CM]
    return out


def route(bundle: dict) -> dict:
    claim = next(e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == "Claim")
    case_id = claim["identifier"][0]["value"]
    service = claim["item"][0]["productOrService"]["text"]
    pol = POLICIES[service]
    dx = diagnoses(bundle)
    if pol["dx_prefix"]:
        if not dx:
            return {"case_id": case_id, "route": "pended", "reason": "missing diagnosis", "policy": pol["policy"]}
        if not any(d.startswith(pol["dx_prefix"]) for d in dx):
            return {"case_id": case_id, "route": "clinical-review", "reason": "diagnosis outside policy", "policy": pol["policy"]}
    return {"case_id": case_id, "route": "clinical-review", "reason": "ready", "policy": pol["policy"]}
