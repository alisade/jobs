"""Structural checks for the PAS-shaped Bundle (given; the tests use it). Not a full IG validator."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ICD10CM = "http://hl7.org/fhir/sid/icd-10-cm"


class Reference(BaseModel):
    reference: str


class Entry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fullUrl: str = Field(pattern=r"^urn:uuid:[0-9a-f-]{36}$")
    resource: dict[str, Any]


class Bundle(BaseModel):
    resourceType: Literal["Bundle"]
    type: Literal["collection"]
    entry: list[Entry] = Field(min_length=6)


def refs(obj: Any) -> list[str]:
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "reference" and isinstance(v, str):
                out.append(v)
            else:
                out.extend(refs(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(refs(v))
    return out


def problems(bundle: dict) -> list[str]:
    """Return a list of problems; empty means the Bundle passes these structural checks."""
    out: list[str] = []
    b = Bundle.model_validate(bundle)
    urls = {e.fullUrl for e in b.entry}
    if len(urls) != len(b.entry):
        out.append("duplicate fullUrl")
    for e in b.entry:
        for r in refs(e.resource):
            if r not in urls:
                out.append(f"{e.resource.get('resourceType')} has unresolved reference {r}")
    types = [e.resource.get("resourceType") for e in b.entry]
    for need in ("Claim", "Patient", "Coverage", "Condition", "Practitioner", "Organization"):
        if need not in types:
            out.append(f"missing {need}")
    claims = [e.resource for e in b.entry if e.resource.get("resourceType") == "Claim"]
    if len(claims) != 1:
        out.append("exactly one Claim required")
    else:
        c = claims[0]
        if c.get("use") != "preauthorization":
            out.append("Claim.use must be preauthorization")
        for f in ("patient", "provider", "insurer", "priority", "insurance", "item", "diagnosis", "created"):
            if f not in c:
                out.append(f"Claim.{f} missing")
    for e in b.entry:
        r = e.resource
        if r.get("resourceType") == "Condition":
            sys = [c.get("system") for c in r.get("code", {}).get("coding", [])]
            if ICD10CM not in sys:
                out.append("Condition without an ICD-10-CM coding")
    return out
