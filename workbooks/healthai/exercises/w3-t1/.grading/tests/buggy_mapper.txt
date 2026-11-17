"""Map normalized intake records to FHIR resources for the PA engine."""

from __future__ import annotations

from . import terminology as T


def icd_display_code(code: str) -> str:
    code = code.strip().upper().replace(".", "")
    return code if len(code) <= 3 else f"{code[:3]}.{code[3:]}"


def to_bundle(rec: dict) -> dict:
    pat = f"urn:uuid:{rec['case_id']}-patient"
    entries = [
        {"fullUrl": pat, "resource": {"resourceType": "Patient", "identifier": [{"value": rec["member_id"]}]}},
        {"fullUrl": f"urn:uuid:{rec['case_id']}-coverage", "resource": {
            "resourceType": "Coverage", "status": "active", "beneficiary": {"reference": pat},
            "payor": [{"identifier": {"value": "KHP01"}}]}},
        {"fullUrl": f"urn:uuid:{rec['case_id']}-claim", "resource": {
            "resourceType": "Claim", "use": "preauthorization", "identifier": [{"value": rec["case_id"]}],
            "patient": {"reference": pat}, "item": [{"sequence": 1, "productOrService": {"text": rec["service"]}}]}},
    ]
    for i, code in enumerate(rec.get("diagnoses", [])):
        entries.append({"fullUrl": f"urn:uuid:{rec['case_id']}-dx{i}", "resource": {
            "resourceType": "Condition", "subject": {"reference": pat},
            "code": {"coding": [{"system": T.ICD10, "code": icd_display_code(code)}]}}})
    return {"resourceType": "Bundle", "type": "collection", "entry": entries}
