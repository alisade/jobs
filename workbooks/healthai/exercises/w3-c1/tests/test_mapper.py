from pathlib import Path

from pas.bundle_check import problems
from pas.mapper import to_pas_bundle

FIX = Path(__file__).resolve().parent.parent / "fixtures"


def res(bundle, kind):
    return [e["resource"] for e in bundle["entry"] if e["resource"]["resourceType"] == kind]


def test_standard_request_maps_to_a_valid_bundle():
    bundle, _ = to_pas_bundle((FIX / "278_req_001.x12").read_text())
    assert problems(bundle) == []
    claim = res(bundle, "Claim")[0]
    assert claim["use"] == "preauthorization"
    assert res(bundle, "Patient")[0]["identifier"][0]["value"] == "M-100201"


def test_diagnosis_code_gets_its_dot():
    bundle, _ = to_pas_bundle((FIX / "278_req_001.x12").read_text())
    assert res(bundle, "Condition")[0]["code"]["coding"][0] == {"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "M54.16"}
