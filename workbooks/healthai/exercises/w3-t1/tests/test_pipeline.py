"""Visible tests. Also add tests/test_regression.py (see README)."""

from pipeline.criteria_engine import route
from pipeline.mapper import to_bundle

REC = {"case_id": "PA-2026-1", "member_id": "M-100201", "service": "cardiac-pet", "diagnoses": ["I2510"]}


def test_lumbar_mri_without_dx_rule_is_ready():
    b = to_bundle({**REC, "service": "lumbar-mri", "diagnoses": ["M5416"]})
    assert route(b)["route"] == "clinical-review"


def test_cardiac_case_with_diagnosis_is_ready():
    assert route(to_bundle(REC))["reason"] == "ready"
