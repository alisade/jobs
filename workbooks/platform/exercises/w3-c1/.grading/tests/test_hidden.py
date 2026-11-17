"""Hidden tests for platform/w3-c1."""
import copy
import json
import random
import subprocess
import sys
from pathlib import Path

import hcl2
import pytest

import importgen

ROOT = Path.cwd()
INV = ROOT / "inventory"
ASSETS = json.loads((INV / "cai-export.json").read_text())["assets"]
STATE = json.loads((INV / "state-ids.json").read_text())
PROJ = json.loads((INV / "projects.json").read_text())


def gen(assets=None, state=None):
    return importgen.generate(copy.deepcopy(assets or ASSETS), STATE if state is None else state, PROJ)


def blocks(res):
    out = {}
    for rel, text in res["files"].items():
        for imp in hcl2.loads(text).get("import", []):
            out[imp["to"].strip("${}")] = (rel, imp["id"])
    return out


EXPECTED = {
    "google_compute_network.riq_legacy": ("riq/imports.tf", "projects/tsl-riq-prod/global/networks/riq-legacy"),
    "google_compute_network.mdm_peering": ("mdm/imports.tf", "projects/tsl-riq-prod/global/networks/mdm-peering"),
    "google_compute_subnetwork.riq_usc1": ("riq/imports.tf", "projects/tsl-riq-prod/regions/us-central1/subnetworks/riq-usc1"),
    "google_compute_subnetwork.riq_use4": ("riq/imports.tf", "projects/tsl-riq-prod/regions/us-east4/subnetworks/riq-use4"),
    "google_compute_firewall.allow_iap_ssh": ("platform/imports.tf", "projects/tsl-riq-prod/global/firewalls/allow-iap-ssh"),
    "google_storage_bucket.tsl_riq_exports": ("riq/imports.tf", "tsl-riq-prod/tsl-riq-exports"),
    "google_storage_bucket.tsl_riq_models_v2": ("riq-ml/imports.tf", "tsl-riq-prod/tsl-riq-models.v2"),
    "google_service_account.riq_api": ("platform/imports.tf", "projects/tsl-riq-prod/serviceAccounts/riq-api@tsl-riq-prod.iam.gserviceaccount.com"),
    "google_service_account.r_9riq_batch": ("platform/imports.tf", "projects/tsl-riq-prod/serviceAccounts/9riq-batch@tsl-riq-prod.iam.gserviceaccount.com"),
    "google_sql_database_instance.riq_legacy_pg": ("riq/imports.tf", "projects/tsl-riq-prod/instances/riq-legacy-pg"),
    "google_project_iam_member.container_developer_riq_devs": ("platform/imports.tf", "tsl-riq-prod roles/container.developer group:riq-devs@tessellate.example"),
    "google_project_iam_member.cloudsql_client_riq_devs": ("platform/imports.tf", "tsl-riq-prod roles/cloudsql.client group:riq-devs@tessellate.example"),
    "google_project_iam_member.cloudsql_client_riq_api": ("platform/imports.tf", "tsl-riq-prod roles/cloudsql.client serviceAccount:riq-api@tsl-riq-prod.iam.gserviceaccount.com"),
}


def test_exact_blocks():
    assert blocks(gen()) == EXPECTED


def test_report():
    r = gen()["report"]
    assert sorted(r["already_managed"]) == sorted(STATE.values())
    assert [u["name"] for u in r["unsupported"]] == ["//pubsub.googleapis.com/projects/tsl-riq-prod/topics/riq-events"]
    reasons = " ".join(s["name"] for s in r["skipped"])
    assert "networks/default" in reasons and "cloudservices" in reasons and "container-engine-robot" in reasons
    assert any("compute@developer" in s["reason"] for s in r["skipped"])


@pytest.mark.parametrize("raw,want", [("riq-legacy", "riq_legacy"), ("9riq-batch", "r_9riq_batch"),
                                      ("Tsl.Models--v2", "tsl_models_v2"), ("__a__", "a")])
def test_ident(raw, want):
    assert importgen.ident(raw) == want


def test_collisions_are_stable():
    extra = [{"name": f"//compute.googleapis.com/projects/tsl-riq-prod/global/firewalls/{n}", "assetType": "compute.googleapis.com/Firewall",
              "resource": {"parent": "//cloudresourcemanager.googleapis.com/projects/530118224466", "data": {"name": n}}}
             for n in ("allow-ssh", "allow.ssh", "allow_ssh")]
    b = blocks(gen(ASSETS + extra))
    names = {k: v[1].rsplit("/", 1)[-1] for k, v in b.items() if k.startswith("google_compute_firewall.allow_ssh")}
    assert names == {"google_compute_firewall.allow_ssh": "allow-ssh", "google_compute_firewall.allow_ssh_2": "allow.ssh",
                     "google_compute_firewall.allow_ssh_3": "allow_ssh"}


def test_byte_stable_and_order_independent():
    a = gen()["files"]
    shuffled = copy.deepcopy(ASSETS)
    random.Random(7).shuffle(shuffled)
    assert gen(shuffled)["files"] == a == gen()["files"]


def test_nothing_managed_imports_everything_supported():
    b = blocks(gen(state={}))
    assert "google_compute_firewall.allow_health_checks" in b
    assert any(v[1].endswith("roles/logging.logWriter serviceAccount:riq-api@tsl-riq-prod.iam.gserviceaccount.com") for v in b.values())


def test_cli_writes_files(tmp_path):
    p = subprocess.run([sys.executable, str(ROOT / "importgen.py"), "--inventory", str(INV), "--out", str(tmp_path)],
                       capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    assert (tmp_path / "riq" / "imports.tf").exists() and json.loads((tmp_path / "report.json").read_text())
