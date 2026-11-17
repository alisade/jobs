"""Parse a 278-like request (see README for the simplified segment spec) and map it to a PAS-shaped Bundle."""

from __future__ import annotations

import re
import uuid
from datetime import date

ICD10CM = "http://hl7.org/fhir/sid/icd-10-cm"
NPI = "http://hl7.org/fhir/sid/us-npi"
MEMBER = "https://kestrel-health.example/fhir/sid/member-id"
NS = uuid.UUID("6f1d6a1c-3b1e-4a55-9f3e-2f0c5e7d9a10")


class X12Error(ValueError):
    pass


def parse_x12(text: str) -> list[list[str]]:
    text = text.lstrip()
    if not text.startswith("ISA") or len(text) < 106:
        raise X12Error("not an interchange: ISA header missing")
    sep = text[3]
    parts = text.split(sep, 16)
    if len(parts) < 17 or len(parts[16]) < 2:
        raise X12Error("ISA header is truncated")
    term = parts[16][1]
    segs = []
    for raw in text.split(term):
        raw = raw.strip("\r\n ")
        if raw:
            segs.append(raw.split(sep))
    return segs


def d8(value: str) -> str:
    if not re.fullmatch(r"\d{8}", value or ""):
        raise X12Error(f"bad CCYYMMDD date {value!r}")
    try:
        return date(int(value[:4]), int(value[4:6]), int(value[6:])).isoformat()
    except ValueError as exc:
        raise X12Error(f"bad CCYYMMDD date {value!r}") from exc


def icd(code: str) -> str:
    code = code.strip().upper().replace(".", "")
    return code if len(code) <= 3 else f"{code[:3]}.{code[3:]}"


def el(seg: list[str], i: int) -> str:
    return seg[i] if len(seg) > i else ""


def to_pas_bundle(text: str) -> tuple[dict, list[str]]:
    segs = parse_x12(text)
    warnings: list[str] = []
    bht = next((s for s in segs if s[0] == "BHT"), None)
    if not bht:
        raise X12Error("BHT segment missing")
    trace = el(bht, 3)
    names = {el(s, 1): s for s in segs if s[0] == "NM1"}
    for code, what in (("X3", "payer"), ("1P", "requesting provider"), ("IL", "subscriber/member")):
        if code not in names:
            raise X12Error(f"NM1*{code} ({what}) missing")
    dmg = next((s for s in segs if s[0] == "DMG"), None)
    um = next((s for s in segs if s[0] == "UM"), None)
    hi = next((s for s in segs if s[0] == "HI"), None)
    dtp = next((s for s in segs if s[0] == "DTP" and el(s, 1) == "472"), None)
    if not um:
        raise X12Error("UM segment missing")
    if not hi or len(hi) < 2:
        raise X12Error("HI segment (diagnosis) missing")

    def url(kind: str, key: str = "") -> str:
        return f"urn:uuid:{uuid.uuid5(NS, f'{trace}/{kind}/{key}')}"

    payer, prov, sub = names["X3"], names["1P"], names["IL"]
    org_u, prac_u, pat_u, cov_u, sr_u, claim_u = (url("Organization"), url("Practitioner"), url("Patient"),
                                                  url("Coverage"), url("ServiceRequest"), url("Claim"))
    patient = {"resourceType": "Patient",
               "identifier": [{"system": MEMBER, "value": el(sub, 9)}],
               "name": [{"family": el(sub, 3).title(), "given": [el(sub, 4).title()]}]}
    if dmg:
        patient["birthDate"] = d8(el(dmg, 2))
        patient["gender"] = {"M": "male", "F": "female"}.get(el(dmg, 3), "unknown")
    else:
        warnings.append("DMG missing: Patient.birthDate and gender omitted")
    org = {"resourceType": "Organization", "name": el(payer, 3).title(),
           "identifier": [{"system": "https://kestrel-health.example/fhir/sid/payer-id", "value": el(payer, 9)}]}
    prac = {"resourceType": "Practitioner", "identifier": [{"system": NPI, "value": el(prov, 9)}],
            "name": [{"family": el(prov, 3).title(), "given": [el(prov, 4).title()]}]}
    coverage = {"resourceType": "Coverage", "status": "active", "subscriberId": el(sub, 9),
                "beneficiary": {"reference": pat_u}, "payor": [{"reference": org_u}]}
    warnings.append("278 carries no coverage period: Coverage.period omitted")
    conditions = []
    for i, comp in enumerate(hi[1:]):
        qual, _, code = comp.partition(":")
        if qual not in ("ABK", "ABF") or not code:
            raise X12Error(f"bad HI composite {comp!r}")
        conditions.append((url("Condition", str(i)), {
            "resourceType": "Condition", "subject": {"reference": pat_u},
            "code": {"coding": [{"system": ICD10CM, "code": icd(code)}]},
        }, qual))
    conditions.sort(key=lambda c: c[2] != "ABK")
    label = el(um, 3)
    warnings.append("service is a generic label, not a coded procedure: productOrService.text only")
    item = {"sequence": 1, "productOrService": {"text": label}}
    if dtp:
        if el(dtp, 2) == "D8":
            item["servicedDate"] = d8(el(dtp, 3))
        elif el(dtp, 2) == "RD8":
            a, _, b = el(dtp, 3).partition("-")
            item["servicedPeriod"] = {"start": d8(a), "end": d8(b)}
        else:
            raise X12Error(f"unknown DTP format {el(dtp, 2)!r}")
    expedited = el(um, 4) == "U"
    if expedited:
        warnings.append("UM level of service U mapped to Claim.priority stat")
    sr = {"resourceType": "ServiceRequest", "status": "active", "intent": "order", "code": {"text": label},
          "subject": {"reference": pat_u}, "requester": {"reference": prac_u}}
    claim = {
        "resourceType": "Claim", "status": "active", "use": "preauthorization",
        "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/claim-type", "code": "professional"}]},
        "created": d8(el(bht, 4)), "identifier": [{"value": trace}],
        "patient": {"reference": pat_u}, "provider": {"reference": prac_u}, "insurer": {"reference": org_u},
        "priority": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/processpriority",
                                 "code": "stat" if expedited else "normal"}]},
        "diagnosis": [{"sequence": n + 1, "diagnosisReference": {"reference": u}} for n, (u, _, _) in enumerate(conditions)],
        "insurance": [{"sequence": 1, "focal": True, "coverage": {"reference": cov_u}}],
        "supportingInfo": [{"sequence": 1, "category": {"text": "service request"}, "valueReference": {"reference": sr_u}}],
        "item": [item],
    }
    entries = [(claim_u, claim), (pat_u, patient), (cov_u, coverage), (org_u, org), (prac_u, prac), (sr_u, sr)]
    entries += [(u, r) for u, r, _ in conditions]
    return {"resourceType": "Bundle", "type": "collection",
            "entry": [{"fullUrl": u, "resource": r} for u, r in entries]}, warnings
