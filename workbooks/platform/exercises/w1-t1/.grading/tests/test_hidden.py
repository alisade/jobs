"""Hidden tests for platform/w1-t1."""
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "tools"))
import wifsim  # noqa: E402

INFRA = wifsim.load_infra(ROOT / "infra")
CLAIMS = json.loads((Path(__file__).parent / "claims_hidden.json").read_text())

APPLY = {"apply_main_prod": True, "pr": False, "feature_push": False, "main_push_no_env": False,
         "staging_env": False, "other_repo_prod": False, "fork_owner": False}
PLAN = {"pr": True, "feature_push": True, "fork_owner": False}


@pytest.mark.parametrize("case,allowed", sorted(APPLY.items()))
def test_apply_sa_matrix(case, allowed):
    res = wifsim.simulate(INFRA, CLAIMS[case], "tf-apply")
    assert res["allowed"] is allowed, (case, res)


@pytest.mark.parametrize("case,allowed", sorted(PLAN.items()))
def test_plan_sa_matrix(case, allowed):
    res = wifsim.simulate(INFRA, CLAIMS[case], "tf-plan")
    assert res["allowed"] is allowed, (case, res)


def test_provider_condition_still_pins_owner():
    p = INFRA["resource"]["google_iam_workload_identity_pool_provider"]["github"]
    cond = p.get("attribute_condition") or ""
    assert re.search(r"assertion\.repository_owner(_id)?\s*==", cond) or "assertion.repository ==" in cond


def test_apply_binding_is_not_pool_or_repo_wide():
    members = []
    for kind in ("google_service_account_iam_member", "google_service_account_iam_binding"):
        for b in INFRA["resource"].get(kind, {}).values():
            if "tf-apply@" in b.get("service_account_id", "") and b.get("role") == "roles/iam.workloadIdentityUser":
                members += [b["member"]] if "member" in b else list(b.get("members") or [])
    assert members, "tf-apply must still have a workloadIdentityUser binding"
    for m in members:
        assert not m.endswith("/*"), m
        assert "/attribute.repository/" not in m and "/attribute.repository_owner/" not in m, m


def test_apply_job_keeps_production_environment():
    wf = yaml.safe_load((ROOT / "ci" / "foundation.yml").read_text())
    assert wf["jobs"]["apply"].get("environment") in ("production", {"name": "production"})
