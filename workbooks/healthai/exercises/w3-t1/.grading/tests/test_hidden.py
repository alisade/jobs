"""Hidden tests for healthai/w3-t1."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from pipeline import terminology as T
from pipeline.criteria_engine import diagnoses, route
from pipeline.mapper import to_bundle
from pipeline.run import run

WORK = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent


@pytest.fixture(scope="module")
def requests(tmp_path_factory):
    d = tmp_path_factory.mktemp("d")
    subprocess.run([sys.executable, str(WORK / "scripts" / "generate.py"), str(d)], check=True, timeout=60)
    return d / "requests.json"


def test_mapper_emits_icd10cm():
    b = to_bundle({"case_id": "PA-H-1", "member_id": "M-1", "service": "chemo-infusion", "diagnoses": ["C509", "d0510"]})
    codings = [c for e in b["entry"] if e["resource"]["resourceType"] == "Condition" for c in e["resource"]["code"]["coding"]]
    assert [c["system"] for c in codings] == [T.ICD10CM, T.ICD10CM]
    assert [c["code"] for c in codings] == ["C50.9", "D05.10"]


@pytest.mark.parametrize("svc,dx", [("oncology-pet", ["C3490"]), ("cardiac-cath", ["R079"]), ("cardiac-pet", ["I5023"])])
def test_engine_sees_diagnoses(svc, dx):
    b = to_bundle({"case_id": "PA-H-2", "member_id": "M-1", "service": svc, "diagnoses": dx})
    assert diagnoses(b)
    assert route(b)["reason"] == "ready"


def test_case_without_dx_still_pends_guard():
    b = to_bundle({"case_id": "PA-H-3", "member_id": "M-1", "service": "oncology-pet", "diagnoses": []})
    assert route(b) ["route"] == "pended"


def test_routes_back_to_baseline(requests):
    routes = run(requests)
    pend = sum(1 for r in routes if r["reason"] == "missing diagnosis")
    assert pend == 9


def test_findings():
    f = json.loads((WORK / "findings.json").read_text())
    assert f["root_cause_file"].endswith("mapper.py")
    assert f["wrong_value"] == "http://hl7.org/fhir/sid/icd-10"
    assert f["right_value"] == "http://hl7.org/fhir/sid/icd-10-cm"
    assert f["pended_missing_dx_before_fix"] == 81 and f["pended_missing_dx_after_fix"] == 9


def _run_regression(tmp_path, mapper_src):
    reg = WORK / "tests" / "test_regression.py"
    assert reg.exists(), "add tests/test_regression.py (README step 4)"
    dst = tmp_path / "copy"
    shutil.copytree(WORK / "pipeline", dst / "pipeline")
    (dst / "tests").mkdir()
    shutil.copy(reg, dst / "tests" / "test_regression.py")
    if mapper_src is not None:
        (dst / "pipeline" / "mapper.py").write_text(mapper_src)
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests"],
                          cwd=dst, capture_output=True, text=True, timeout=60).returncode


def test_regression_test_passes_on_fixed_code(tmp_path):
    assert _run_regression(tmp_path, None) == 0


def test_regression_test_fails_on_the_released_mapper(tmp_path):
    assert _run_regression(tmp_path, (HERE / "buggy_mapper.txt").read_text()) != 0
