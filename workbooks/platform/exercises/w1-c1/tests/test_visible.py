"""Visible tests for w1-c1. The hidden suite adds edge cases (deletes, unknown values, conditions)."""
import json
import subprocess
import sys
from pathlib import Path

import guardrails as g

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "plans" / "foundation.plan.json"


def findings():
    return g.evaluate(g.load_plan(PLAN), g.load_policy(ROOT / "policy.yaml"))


def pairs(fs):
    return {(f.rule, f.address) for f in fs}


def test_sa_key_and_default_network_flagged():
    p = pairs(findings())
    assert ("GR001", "google_service_account_key.legacy_ci") in p
    assert ("GR009", 'module.projects["rdm"].google_project.this') in p


def test_basic_role_on_project_flagged():
    assert ("GR002", 'google_project_iam_member.riq_devs["roles/editor"]') in pairs(findings())


def test_predefined_role_not_flagged():
    assert ("GR002", 'google_project_iam_member.riq_devs["roles/container.developer"]') not in pairs(findings())


def test_missing_org_policy_reported():
    msgs = [f.message for f in findings() if f.rule == "GR005"]
    assert any("compute.skipDefaultNetworkCreation" in m for m in msgs)


def test_cli_json_and_exit_code():
    proc = subprocess.run([sys.executable, str(ROOT / "guardrails.py"), str(PLAN), "--json"],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 1
    data = json.loads(proc.stdout)
    assert {"rule", "address", "severity", "message"} <= set(data[0])
