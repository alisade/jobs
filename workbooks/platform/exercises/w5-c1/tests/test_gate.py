"""Visible tests: the shipped render and the CLI contract. Hidden tests cover the edge cases."""
import json
import pathlib

import yaml

import gate

ROOT = pathlib.Path(__file__).resolve().parents[1]
POLICY = yaml.safe_load((ROOT / "config/policy.yaml").read_text())
ATT = json.loads((ROOT / "config/attestations.json").read_text())


def run(paths):
    return gate.evaluate(gate.load_paths([str(ROOT / p) for p in paths]), POLICY, ATT)


def keys(result):
    return {(v["rule"], v["kind"], v["name"]) for v in result["violations"]}


def test_mdm_api_is_clean():
    r = run(["rendered/mdm-api.yaml"])
    assert r["violations"] == [], r["violations"]


def test_shipped_render_findings():
    r = run(["rendered"])
    assert keys(r) == {
        ("IMG001", "CronJob", "riq-reindex"),
        ("IMG002", "CronJob", "riq-reindex"),
        ("IMG003", "StatefulSet", "rdm-worker"),
        ("PDB001", "StatefulSet", "rdm-worker"),
        ("WI002", "ServiceAccount", "rdm-worker"),
    }


def test_finding_shape():
    r = run(["rendered/rdm-worker.yaml"])
    for v in r["violations"]:
        assert set(v) == {"rule", "kind", "name", "namespace", "container", "message"}
        assert v["namespace"] == "rdm"


def test_cli_modes(capsys):
    args = ["--policy", str(ROOT / "config/policy.yaml"), "--attestations", str(ROOT / "config/attestations.json"), str(ROOT / "rendered")]
    assert gate.main(["--mode", "dry-run", *args]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["mode"] == "dry-run" and out["summary"]["violations"] == 5
    assert gate.main(["--mode", "enforce", *args]) == 1
