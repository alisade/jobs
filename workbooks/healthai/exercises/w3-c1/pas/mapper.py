"""Parse a 278-like request and map it to a PAS-shaped Bundle. First draft: see TODOs and README."""

from __future__ import annotations

import uuid

ICD10CM = "http://hl7.org/fhir/sid/icd-10-cm"
NPI = "http://hl7.org/fhir/sid/us-npi"
MEMBER = "https://kestrel-health.example/fhir/sid/member-id"
NS = uuid.UUID("6f1d6a1c-3b1e-4a55-9f3e-2f0c5e7d9a10")


class X12Error(ValueError):
    pass


def parse_x12(text: str) -> list[list[str]]:
    # TODO: take the element separator and segment terminator from the ISA header
    return [s.strip().split("*") for s in text.split("~") if s.strip()]


def to_pas_bundle(text: str) -> tuple[dict, list[str]]:
    """Return (bundle, warnings). Raise X12Error for unusable input."""
    segs = parse_x12(text)
    sub = next(s for s in segs if s[0] == "NM1" and s[1] == "IL")
    patient = {"resourceType": "Patient", "identifier": [{"system": MEMBER, "value": sub[9]}]}
    # TODO: Claim, Coverage, Condition(s), Practitioner, Organization, ServiceRequest; urn:uuid fullUrls and
    # references that resolve; dates; priority; warnings for what does not map cleanly.
    return {"resourceType": "Bundle", "type": "collection",
            "entry": [{"fullUrl": f"urn:uuid:{uuid.uuid4()}", "resource": patient}]}, []
