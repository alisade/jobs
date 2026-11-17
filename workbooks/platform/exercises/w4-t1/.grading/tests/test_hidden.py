"""Hidden tests for platform/w4-t1."""
import shutil
from pathlib import Path

import yaml

import xpsim

ROOT = Path.cwd()
RDM = {"apiVersion": "platform.tessellate.example/v1alpha1", "kind": "AppDatabase",
       "metadata": {"name": "rdm-ref", "namespace": "team-rdm"},
       "spec": {"size": "large", "version": "postgres-16", "team": "rdm"}}


def run_with_new_team(tmp_path):
    t = tmp_path / "teams"
    shutil.copytree(ROOT / "teams", t)
    (t / "team-rdm").mkdir(exist_ok=True)
    (t / "team-rdm" / "rdm.yaml").write_text(yaml.safe_dump(RDM))
    return xpsim.run(ROOT / "platform", t)


def by_xr(res):
    return {x["xr"]: x for x in res["xrs"]}


def test_new_team_namespace_works_without_extra_config(tmp_path):
    res = by_xr(run_with_new_team(tmp_path))
    assert res["team-rdm/rdm-ref"]["Ready"], res["team-rdm/rdm-ref"]["message"]
    assert all(x["Ready"] for x in res.values())


def test_composition_mappings_intact(tmp_path):
    res = by_xr(run_with_new_team(tmp_path))
    inst = next(r for r in res["team-rdm/rdm-ref"]["resources"] if r["kind"] == "DatabaseInstance")
    fp = inst["spec"]["forProvider"]
    assert fp["settings"][0]["tier"] == "db-custom-8-30720" and fp["databaseVersion"] == "POSTGRES_16"
    assert fp["deletionProtection"] is True and inst["spec"]["deletionPolicy"] == "Orphan"
    user = next(r for r in res["team-rdm/rdm-ref"]["resources"] if r["kind"] == "User")
    assert user["spec"]["writeConnectionSecretToRef"]["name"] == "rdm-ref-db-conn"
    assert user["namespace"] == "team-rdm"


def test_v2_shape_kept():
    docs = xpsim.load([ROOT / "platform", ROOT / "teams"])
    kinds = {d["kind"] for d in docs}
    assert not any(k.endswith("Claim") for k in kinds)
    xrd = next(d for d in docs if d["kind"] == "CompositeResourceDefinition")
    assert xrd["spec"]["scope"] == "Namespaced" and "claimNames" not in xrd["spec"]
    comp = next(d for d in docs if d["kind"] == "Composition")
    assert comp["spec"]["mode"] == "Pipeline"


def test_shared_config_still_workload_identity():
    docs = xpsim.load([ROOT / "platform"])
    cpc = [d for d in docs if d["kind"] == "ClusterProviderConfig"]
    assert cpc and cpc[0]["spec"]["credentials"]["source"] == "InjectedIdentity"
    assert not any(d["kind"] == "ProviderConfig" and (d["spec"].get("credentials") or {}).get("source") == "Secret" for d in docs)
