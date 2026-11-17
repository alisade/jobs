"""Hidden tests for platform/w1-c1."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

import guardrails as g

ROOT = Path.cwd()
POLICY = g.load_policy(ROOT / "policy.yaml")


def rc(typ, after, address=None, actions=("create",), unknown=None, mode="managed"):
    return {"address": address or f"{typ}.x", "mode": mode, "type": typ,
            "change": {"actions": list(actions), "before": None, "after": after, "after_unknown": unknown or {}}}


def run(*rcs):
    return g.evaluate({"format_version": "1.2", "resource_changes": list(rcs)}, POLICY)


def rules_of(fs, sev=None):
    return sorted({f.rule for f in fs if sev is None or f.severity == sev})


ALL_ORG = [
    rc("google_org_policy_policy", {"name": f"organizations/812345678901/policies/{c}", "parent": "organizations/812345678901",
                                    "spec": [{"rules": [{"enforce": "TRUE"}]}]}, address=f'p["{c}"]')
    for c in ("iam.disableServiceAccountKeyCreation", "storage.uniformBucketLevelAccess", "compute.skipDefaultNetworkCreation")
] + [
    rc("google_org_policy_policy", {"name": "organizations/812345678901/policies/compute.vmExternalIpAccess",
                                    "parent": "organizations/812345678901", "spec": [{"rules": [{"deny_all": "TRUE"}]}]}, address="p_ext"),
    rc("google_org_policy_policy", {"name": "organizations/812345678901/policies/gcp.resourceLocations",
                                    "parent": "organizations/812345678901",
                                    "spec": [{"rules": [{"values": [{"allowed_values": ["in:us-central1-locations", "in:us-east4-locations"]}]}]}]},
       address="p_loc"),
]


def test_fixture_exact_findings():
    fs = g.evaluate(g.load_plan(ROOT / "plans" / "foundation.plan.json"), POLICY)
    got = {(f.rule, f.address) for f in fs if f.severity == "error"}
    want = {
        ("GR001", "google_service_account_key.legacy_ci"),
        ("GR002", 'google_project_iam_member.riq_devs["roles/editor"]'),
        ("GR003", "google_folder_iam_member.workloads_viewer"),
        ("GR004", "google_iam_workload_identity_pool_provider.github_legacy"),
        ("GR005", 'google_org_policy_policy.org["gcp.resourceLocations"]'),
        ("GR005", 'google_org_policy_policy.org["storage.uniformBucketLevelAccess"]'),
        ("GR005", "organizations/812345678901 (org policies)"),
        ("GR006", 'google_compute_subnetwork.subnets["core-euw1"]'),
        ("GR006", 'google_compute_subnetwork.subnets["core-usc1-gke"]'),
        ("GR007", "google_storage_bucket.riq_exports"),
        ("GR008", 'module.projects["rdm"].google_project.this'),
        ("GR009", 'module.projects["rdm"].google_project.this'),
    }
    assert got == want


def test_complete_org_policy_set_is_clean():
    assert run(*ALL_ORG) == []


def test_deletes_and_data_sources_ignored():
    fs = run(*ALL_ORG,
             rc("google_service_account_key", None, actions=("delete",)),
             rc("google_project_iam_member", {"project": "p", "role": "roles/owner", "member": "user:a@x"}, mode="data"))
    assert fs == []


def test_basic_role_binding_on_folder():
    fs = run(*ALL_ORG, rc("google_folder_iam_binding", {"folder": "folders/1", "role": "roles/owner",
                                                        "members": ["group:g@tessellate.example"]}))
    assert rules_of(fs) == ["GR002"]


def test_user_on_org_binding_but_not_on_project():
    fs = run(*ALL_ORG,
             rc("google_organization_iam_binding", {"org_id": "812345678901", "role": "roles/billing.viewer",
                                                    "members": ["group:fin@tessellate.example", "user:marco.d@tessellate.example"]}, address="org_b"),
             rc("google_project_iam_member", {"project": "tsl-riq-prod", "role": "roles/logging.viewer",
                                              "member": "user:priya.n@tessellate.example"}, address="proj_m"))
    assert {(f.rule, f.address) for f in fs} == {("GR003", "org_b")}


GH = [{"issuer_uri": "https://token.actions.githubusercontent.com"}]


@pytest.mark.parametrize("cond,bad", [
    (None, True),
    ("", True),
    ("assertion.repository_owner == 'tessellate'", False),
    ("assertion.repository == 'tessellate/platform-foundation' && assertion.ref == 'refs/heads/main'", False),
    ("assertion.repository_owner_id == '91234567'", False),
    ("assertion.repository_owner == 'evilcorp'", True),
    ("assertion.repository_owner == 'tessellate' || assertion.actor == 'bot'", True),
    ("assertion.event_name == 'push'", True),
])
def test_wif_conditions(cond, bad):
    fs = run(*ALL_ORG, rc("google_iam_workload_identity_pool_provider", {"attribute_condition": cond, "oidc": GH}))
    assert (rules_of(fs, "error") == ["GR004"]) is bad


def test_wif_non_github_issuer_ignored_and_unknown_is_warning():
    other = rc("google_iam_workload_identity_pool_provider",
               {"attribute_condition": None, "oidc": [{"issuer_uri": "https://gitlab.tessellate.example"}]}, address="gl")
    unk = rc("google_iam_workload_identity_pool_provider", {"oidc": GH}, address="unk",
             unknown={"attribute_condition": True})
    fs = run(*ALL_ORG, other, unk)
    assert [(f.rule, f.address, f.severity) for f in fs] == [("GR004", "unk", "warning")]


def test_org_policy_shapes():
    org = [x for x in ALL_ORG if x["address"] not in ("p_ext", "p_loc")]
    ext_wrong = rc("google_org_policy_policy", {"name": "organizations/812345678901/policies/compute.vmExternalIpAccess",
                                                "parent": "organizations/812345678901", "spec": [{"rules": [{"enforce": "TRUE"}]}]}, address="p_ext")
    loc_folder = rc("google_org_policy_policy", {"name": "folders/77/policies/gcp.resourceLocations", "parent": "folders/77",
                                                 "spec": [{"rules": [{"values": [{"allowed_values": ["in:us-east4-locations"]}]}]}]}, address="p_loc_folder")
    fs = run(*org, ext_wrong, loc_folder)
    got = {(f.rule, f.address) for f in fs}
    assert ("GR005", "p_ext") in got
    assert ("GR005", "organizations/812345678901 (org policies)") in got  # folder-level policy does not count
    assert all(f.rule == "GR005" for f in fs)


def test_subnet_unknown_region_is_warning_only():
    fs = run(*ALL_ORG, rc("google_compute_subnetwork", {"private_ip_google_access": True}, unknown={"region": True}))
    assert [(f.rule, f.severity) for f in fs] == [("GR006", "warning")]


@pytest.mark.parametrize("loc,ok", [("us-east4", True), ("US-CENTRAL1", True), ("US", True), ("EU", False), ("asia-south1", False)])
def test_bucket_locations(loc, ok):
    fs = run(*ALL_ORG, rc("google_storage_bucket", {"location": loc, "uniform_bucket_level_access": True,
                                                    "public_access_prevention": "enforced"}))
    assert (fs == []) is ok


def test_shared_vpc_attachment_to_non_host_and_unknown():
    host = rc("google_compute_shared_vpc_host_project", {"project": "tsl-net-host-prod"}, address="host")
    bad = rc("google_compute_shared_vpc_service_project", {"host_project": "tsl-net-host-stg", "service_project": "tsl-mdm-prod"}, address="bad")
    unk = rc("google_compute_shared_vpc_service_project", {"service_project": "tsl-riq-prod"}, address="unk",
             unknown={"host_project": True})
    proj = rc("google_project", {"project_id": "tsl-riq-prod", "labels": {"network": "shared"}, "auto_create_network": False}, address="proj")
    fs = run(*ALL_ORG, host, bad, unk, proj)
    got = {(f.rule, f.address, f.severity) for f in fs}
    assert got == {("GR008", "bad", "error"), ("GR008", "unk", "warning")}


def test_cli_bad_input_exit_2(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    proc = subprocess.run([sys.executable, str(ROOT / "guardrails.py"), str(bad)], capture_output=True, text=True, timeout=60)
    assert proc.returncode == 2


def test_cli_clean_plan_exit_0(tmp_path):
    p = tmp_path / "clean.json"
    p.write_text(json.dumps({"format_version": "1.2", "resource_changes": ALL_ORG}))
    proc = subprocess.run([sys.executable, str(ROOT / "guardrails.py"), str(p)], capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
