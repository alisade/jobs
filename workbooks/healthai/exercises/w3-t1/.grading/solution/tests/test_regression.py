"""Regression for INC-48390: diagnoses must be coded in ICD-10-CM, and the engine must see them."""

from pipeline import terminology as T
from pipeline.criteria_engine import diagnoses, route
from pipeline.mapper import to_bundle


def test_conditions_use_icd10cm_and_engine_sees_them():
    b = to_bundle({"case_id": "PA-R-1", "member_id": "M-100201", "service": "oncology-pet", "diagnoses": ["C3490"]})
    systems = [c["system"] for e in b["entry"] if e["resource"]["resourceType"] == "Condition"
               for c in e["resource"]["code"]["coding"]]
    assert systems == [T.ICD10CM]
    assert diagnoses(b) == ["C34.90"]
    assert route(b)["reason"] == "ready"
