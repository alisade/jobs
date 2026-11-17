"""Visible tests for w1-t1: the recorded runs through the local WIF simulator."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import wifsim  # noqa: E402

INFRA = wifsim.load_infra(ROOT / "infra")


def claims(name):
    return json.loads((ROOT / "evidence" / "claims" / name).read_text())


def test_pr_plan_job_gets_plan_sa():
    assert wifsim.simulate(INFRA, claims("plan-run-4409.json"), "tf-plan")["allowed"]


def test_production_apply_job_gets_apply_sa():
    res = wifsim.simulate(INFRA, claims("apply-run-4412.json"), "tf-apply")
    assert res["allowed"], res


def test_pr_job_cannot_get_apply_sa():
    assert not wifsim.simulate(INFRA, claims("plan-run-4409.json"), "tf-apply")["allowed"]
