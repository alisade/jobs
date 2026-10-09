"""Visible tests for the FieldOps UAT release."""

import json
from pathlib import Path

import yaml

import preflight as pf

ROOT = Path(__file__).resolve().parent.parent


def load():
    manifest = yaml.safe_load((ROOT / "deploy" / "manifest.yaml").read_text())
    inventory = json.loads((ROOT / "deploy" / "environments" / "uat.json").read_text())
    artifacts = json.loads((ROOT / "deploy" / "artifacts.json").read_text())
    xml = (ROOT / "solutions" / "FieldOps" / "src" / "Other" / "Solution.xml").read_text()
    return manifest, inventory, artifacts, {"FieldOps": xml}


def test_manifest_still_ships_fieldops_1_4_managed():
    manifest = load()[0]
    steps = [s for s in manifest["solutions"] if s["name"] == "FieldOps"]
    assert steps and steps[0]["version"] == "1.4.0.0" and steps[0]["managed"] is True


def test_parse_version_is_numeric():
    assert pf.parse_version("2.10.0.0") > pf.parse_version("2.9.5.0")


def test_missing_dependencies_parsed():
    xml = load()[3]["FieldOps"]
    deps = pf.missing_dependencies(xml)
    assert any(d["required"] == "contoso_regioncode" and d["solution_name"] == "ContosoCore" for d in deps)


def test_preflight_passes_for_the_release():
    assert pf.preflight(*load()) == []
