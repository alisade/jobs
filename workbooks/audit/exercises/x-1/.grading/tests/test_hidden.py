"""Hidden tests for audit/x-1: the right identity works, nothing else does, no over-broad grants."""

from __future__ import annotations

import json

import pytest

from wifsim.sim import simulate

TENANT = "7c1e4b2a-5d3f-4e81-9a6c-2b0d8f4e1a37"
APP = "api://b6d0a3f2-41c9-4e7a-9b5d-0e8c2f71a6d4"
NUM = "418203557719"


def load(config_dir, name):
    return json.loads((config_dir / name).read_text())


def test_function_identity_reaches_gemini(claims, config_dir):
    r = simulate(claims, config_dir)
    assert r.ok and r.stage == "done", "\n".join(r.lines)


def test_other_managed_identity_in_same_tenant_is_denied(claims, config_dir):
    other = dict(claims, sub="0b7e1d44-9c2a-4f60-a3e8-51d9c6b2e7f0", oid="0b7e1d44-9c2a-4f60-a3e8-51d9c6b2e7f0",
                 appid="c4f2a9e1-7b3d-4a05-8e6c-92d1f0b4a738")
    r = simulate(other, config_dir)
    assert not r.ok and r.stage in ("sts_exchange", "impersonation")


def test_same_client_id_but_other_object_is_denied(claims, config_dir):
    other = dict(claims, sub="0b7e1d44-9c2a-4f60-a3e8-51d9c6b2e7f0", oid="0b7e1d44-9c2a-4f60-a3e8-51d9c6b2e7f0")
    assert not simulate(other, config_dir).ok


def test_other_tenant_is_rejected(claims, config_dir):
    t = "11111111-2222-3333-4444-555555555555"
    r = simulate(dict(claims, tid=t, iss=f"https://sts.windows.net/{t}/"), config_dir)
    assert not r.ok and r.stage == "sts_exchange"


def test_condition_still_pins_the_tenant(claims, config_dir):
    r = simulate(dict(claims, tid="11111111-2222-3333-4444-555555555555"), config_dir)
    assert not r.ok and r.stage == "sts_exchange"


def test_wrong_audience_is_rejected(claims, config_dir):
    r = simulate(dict(claims, aud="https://management.azure.com/"), config_dir)
    assert not r.ok


def test_federation_settings_not_loosened(config_dir):
    cred = load(config_dir, "credential-config.json")
    prov = load(config_dir, "wif-provider.json")
    assert cred["type"] == "external_account"
    assert cred["audience"] == f"//iam.googleapis.com/projects/{NUM}/locations/global/workloadIdentityPools/azure-mfh/providers/entra-prod"
    assert f"resource={APP}" in cred["credential_source"]["url"]
    assert prov["oidc"]["allowed_audiences"] == [APP]
    assert prov["oidc"]["issuer_uri"] == f"https://sts.windows.net/{TENANT}/"
    assert TENANT in prov.get("attribute_condition", "")


def test_no_service_account_keys_anywhere(config_dir):
    for p in config_dir.rglob("*.json"):
        text = p.read_text()
        assert "private_key" not in text and '"service_account"' not in text, p.name


@pytest.mark.parametrize("policy", ["sa-iam-policy.json", "project-iam-policy.json"])
def test_no_over_broad_grants(config_dir, policy):
    pol = load(config_dir, policy)
    for b in pol["bindings"]:
        assert b["role"] not in ("roles/owner", "roles/editor", "roles/iam.serviceAccountTokenCreator"), b
        for m in b["members"]:
            assert m not in ("allUsers", "allAuthenticatedUsers"), b
            assert not m.endswith("/*"), f"whole-pool principalSet granted: {m}"
            assert "attribute.tenant/" not in m, f"tenant-wide principalSet granted: {m}"


def test_workload_identity_user_is_one_principal(config_dir):
    pol = load(config_dir, "sa-iam-policy.json")
    members = [m for b in pol["bindings"] if b["role"] == "roles/iam.workloadIdentityUser" for m in b["members"]]
    assert len(members) == 1, members
