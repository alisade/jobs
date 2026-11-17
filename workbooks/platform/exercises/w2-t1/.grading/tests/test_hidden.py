"""Hidden tests for platform/w2-t1."""
import copy
import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path.cwd()
HERE = Path(__file__).parent
sys.path.insert(0, str(ROOT / "tools"))
import drain_sim  # noqa: E402

STATE = json.loads((ROOT / "cluster" / "state.json").read_text())


def scenario(tmp_path, canary="original", state_edit=None):
    k = tmp_path / "k8s"
    shutil.copytree(ROOT / "k8s", k)
    for p in k.rglob("*.yaml"):  # the canary chart belongs to the RIQ team: always their version
        docs = [d for d in yaml.safe_load_all(p.read_text()) if d]
        if any(d.get("kind") == "Deployment" and d["metadata"]["name"] == "riq-api-canary" for d in docs):
            p.unlink()
    if canary in ("original", "healthy"):
        shutil.copy(HERE / "canary_original.yaml", k / "riq" / "zz-canary.yaml")
    st = copy.deepcopy(STATE)
    if canary == "healthy":
        st["broken_controllers"] = []
        for p in st["pods"]:
            if p["controller"] == "riq-api-canary":
                p["ready"] = True
    if canary == "absent":
        st["pods"] = [p for p in st["pods"] if p["controller"] != "riq-api-canary"]
    if state_edit:
        state_edit(st)
    sp = tmp_path / "state.json"
    sp.write_text(json.dumps(st))
    return drain_sim.run(k, sp)


@pytest.mark.parametrize("canary", ["original", "healthy", "absent"])
def test_drains_with_canary(tmp_path, canary):
    res = scenario(tmp_path, canary)
    assert res["complete"], [n for n in res["nodes"] if not n["drained"]]


def test_budget_still_protects_stable_pods(tmp_path):
    def two_unready(st):
        st["broken_controllers"].append("riq/riq-api")  # a bad rollout: replacements crash too
        n = 0
        for p in st["pods"]:
            if p["controller"] == "riq-api" and n < 2:
                p["ready"] = False
                n += 1
    res = scenario(tmp_path, "original", two_unready)
    assert not res["complete"], "with two of four stable pods down the budget must stop the drain"


def test_pdb_selects_exactly_the_stable_pods(tmp_path):
    res = scenario(tmp_path, "original")
    st = {s["name"]: s for s in res["pdbs_before"]}
    assert "riq/riq-api" in st
    assert st["riq/riq-api"]["pods"] == 4 and st["riq/riq-api"]["expected"] == 4
    assert st["riq/riq-api"]["disruptionsAllowed"] == 1


def test_stable_deployment_not_weakened():
    docs = drain_sim.load_manifests(ROOT / "k8s")
    dep = next(d for d in docs if d["kind"] == "Deployment" and d["metadata"]["name"] == "riq-api")
    assert dep["spec"]["replicas"] == 4
    assert "readinessProbe" in dep["spec"]["template"]["spec"]["containers"][0]


def test_mdm_unchanged(tmp_path):
    st = {s["name"]: s for s in scenario(tmp_path, "original")["pdbs_before"]}
    assert (st["mdm/mdm-api"]["desiredHealthy"], st["mdm/rdm-cache"]["desiredHealthy"]) == (2, 2)
