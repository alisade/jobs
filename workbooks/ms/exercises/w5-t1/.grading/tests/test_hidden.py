"""Hidden tests for ms/w5-t1: manifest fix, repo integrity, and the preflight contract."""

import copy
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

import preflight as pf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INV = json.loads((HERE / "uat_ref.json").read_text())
ARTS = json.loads((HERE / "artifacts_ref.json").read_text())
REF_XML = (HERE / "Solution_ref.xml").read_text()


def V(s):
    return tuple(int(x) for x in s.split("."))


def manifest():
    return yaml.safe_load((ROOT / "deploy" / "manifest.yaml").read_text())


# ---------- independent simulation of the release (does not use the learner's preflight) ----------

def required_solutions(xml):
    out = []
    for md in ET.fromstring(xml).iter("MissingDependency"):
        sol = md.find("Required").get("solution", "")
        m = re.match(r"(.+?) \(([\d.]+)\)$", sol)
        out.append((m.group(1), V(m.group(2))) if m else (sol, None))
    return out


def simulate(man):
    state = {s["name"]: (V(s["version"]), s["managed"]) for s in INV["solutions"]}
    arts = {a["file"]: a for a in ARTS["artifacts"]}
    problems = []
    for step in man["solutions"]:
        name, ver, managed = step["name"], V(str(step["version"])), bool(step["managed"])
        a = arts.get(step.get("artifact"))
        if not a or a["solution"] != name or V(a["version"]) != ver or bool(a["managed"]) != managed:
            problems.append(f"bad artifact for {name}")
        if name in state and ver < state[name][0]:
            problems.append(f"downgrade {name}")
        if not managed:
            problems.append(f"unmanaged {name} in UAT")
        if name == "FieldOps":
            for need, nv in required_solutions(REF_XML):
                have = state.get(need)
                if nv is None or have is None or have[0] < nv:
                    problems.append(f"{name} needs {need} {nv}")
        state[name] = (ver, managed)
    return problems, state


def test_release_simulation_succeeds():
    problems, state = simulate(manifest())
    assert problems == [], problems
    assert state["FieldOps"][0] == (1, 4, 0, 0)


def test_core_imported_before_fieldops_at_2_1():
    names = [s["name"] for s in manifest()["solutions"]]
    assert "ContosoCore" in names and names.index("ContosoCore") < names.index("FieldOps")
    core = [s for s in manifest()["solutions"] if s["name"] == "ContosoCore"][0]
    assert V(str(core["version"])) >= (2, 1, 0, 0) and core["managed"] is True


def test_everything_in_uat_is_managed():
    assert all(s["managed"] is True for s in manifest()["solutions"])


def test_fix_did_not_remove_the_feature():
    xml = (ROOT / "solutions" / "FieldOps" / "src" / "Other" / "Solution.xml").read_text()
    cust = (ROOT / "solutions" / "FieldOps" / "src" / "Other" / "Customizations.xml").read_text()
    assert "contoso_regioncode" in cust, "the Region Code form control / view column was removed"
    assert required_solutions(xml) == required_solutions(REF_XML), "Solution.xml dependencies were edited by hand"
    assert re.search(r"<Version>1\.4\.0\.0</Version>", xml)


def test_no_skip_dependency_check_or_unmanaged_shortcut():
    text = (ROOT / "deploy" / "manifest.yaml").read_text()
    assert "skip-dependency-check" not in text and "skip_dependency_check" not in text
    assert "force_overwrite: true" not in text.replace("force-overwrite", "force_overwrite")


# ---------- preflight contract ----------

def test_version_parsing():
    assert pf.parse_version("2.1") == (2, 1, 0, 0)
    assert pf.parse_version("2.10.0.0") > pf.parse_version("2.9.9.9")
    with pytest.raises(ValueError):
        pf.parse_version("2.1.x.0")
    with pytest.raises(ValueError):
        pf.parse_version("1.2.3.4.5")


def test_missing_dependencies_fields():
    deps = pf.missing_dependencies(REF_XML)
    assert len(deps) == 3
    d = [x for x in deps if x["dependent_display"] == "Assets by Region"][0]
    assert d["required"] == "contoso_regioncode" and d["parent"] == "contoso_asset"
    assert d["solution_name"] == "ContosoCore" and d["solution_version"] == (2, 1, 0, 0)
    assert d["required_type"] == 2 and d["dependent_type"] == 26


def test_missing_dependencies_active_and_empty():
    xml = """<ImportExportXml><SolutionManifest><MissingDependencies><MissingDependency>
      <Required type="2" schemaName="new_x" displayName="X" parentSchemaName="account" solution="Active" />
      <Dependent type="60" id="{00000000-0000-0000-0000-000000000001}" displayName="Account" />
    </MissingDependency></MissingDependencies></SolutionManifest></ImportExportXml>"""
    deps = pf.missing_dependencies(xml)
    assert deps[0]["solution_name"] == "Active" and deps[0]["solution_version"] is None
    assert pf.missing_dependencies("<ImportExportXml><SolutionManifest /></ImportExportXml>") == []


BROKEN = {
    "environment": "contoso-fs-uat",
    "solutions": [
        {"name": "FieldOps", "version": "1.4.0.0", "managed": True, "artifact": "FieldOps_1_4_0_0_managed.zip"}
    ],
}


def test_preflight_catches_the_incident():
    errs = pf.preflight(copy.deepcopy(BROKEN), INV, ARTS, {"FieldOps": REF_XML})
    assert errs, "the original manifest must fail preflight"
    joined = " ".join(errs)
    assert "ContosoCore" in joined and "2.1.0.0" in joined and "FieldOps" in joined


def test_preflight_order_matters():
    m = copy.deepcopy(BROKEN)
    m["solutions"].append({"name": "ContosoCore", "version": "2.1.0.0", "managed": True,
                           "artifact": "ContosoCore_2_1_0_0_managed.zip"})
    assert pf.preflight(m, INV, ARTS, {"FieldOps": REF_XML}), "Core after FieldOps is still broken"
    m["solutions"].reverse()
    assert pf.preflight(m, INV, ARTS, {"FieldOps": REF_XML}) == []


def test_preflight_downgrade_and_artifact_checks():
    m = {"solutions": [{"name": "FieldOps", "version": "1.3.0.0", "managed": True,
                        "artifact": "FieldOps_1_3_0_0_managed.zip"}]}
    inv = copy.deepcopy(INV)
    inv["solutions"] = [s if s["name"] != "FieldOps" else {**s, "version": "1.4.0.0"} for s in inv["solutions"]]
    assert any("downgrade" in e.lower() for e in pf.preflight(m, inv, ARTS, {}))
    m2 = {"solutions": [{"name": "ContosoCore", "version": "2.2.0.0", "managed": True,
                         "artifact": "ContosoCore_2_2_0_0_managed.zip"}]}
    assert pf.preflight(m2, INV, ARTS, {}), "artifact that was never built"
    m3 = {"solutions": [{"name": "ContosoCore", "version": "2.1.0.0", "managed": True,
                         "artifact": "ContosoCore_2_1_0_0.zip"}]}
    assert pf.preflight(m3, INV, ARTS, {}), "unmanaged zip shipped as managed"


def test_preflight_managed_over_unmanaged():
    inv = {"solutions": [{"name": "ContosoCore", "version": "2.0.3.0", "managed": False}]}
    m = {"solutions": [{"name": "ContosoCore", "version": "2.1.0.0", "managed": True,
                        "artifact": "ContosoCore_2_1_0_0_managed.zip"}]}
    errs = pf.preflight(m, inv, ARTS, {})
    assert errs and any("unmanaged" in e.lower() for e in errs)


def test_preflight_active_dependency_is_an_error():
    xml = """<ImportExportXml><SolutionManifest><MissingDependencies><MissingDependency>
      <Required type="2" schemaName="new_x" displayName="X" parentSchemaName="account" solution="Active" />
      <Dependent type="60" id="{00000000-0000-0000-0000-000000000001}" displayName="Account" />
    </MissingDependency></MissingDependencies></SolutionManifest></ImportExportXml>"""
    m = {"solutions": [{"name": "FieldOps", "version": "1.4.0.0", "managed": True,
                        "artifact": "FieldOps_1_4_0_0_managed.zip"}]}
    errs = pf.preflight(m, INV, ARTS, {"FieldOps": xml})
    assert errs and "new_x" in " ".join(errs)


def test_preflight_satisfied_by_installed_version():
    xml = REF_XML.replace("ContosoCore (2.1.0.0)", "ContosoCore (2.0.1.0)")
    m = copy.deepcopy(BROKEN)
    assert pf.preflight(m, INV, ARTS, {"FieldOps": xml}) == []


def test_preflight_cli(tmp_path):
    bad = tmp_path / "m.yaml"
    bad.write_text(yaml.safe_dump(BROKEN))
    base = [sys.executable, str(ROOT / "deploy" / "preflight.py"), "--inventory", str(HERE / "uat_ref.json"),
            "--artifacts", str(HERE / "artifacts_ref.json"), "--solutions", str(ROOT / "solutions")]
    r = subprocess.run(base + ["--manifest", str(bad)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 1, r.stdout + r.stderr
    r2 = subprocess.run(base + ["--manifest", str(ROOT / "deploy" / "manifest.yaml")],
                        capture_output=True, text=True, timeout=60)
    assert r2.returncode == 0, r2.stdout + r2.stderr


def test_answer_covers_dependency_and_layering():
    t = (ROOT / "ANSWER.md").read_text().lower()
    assert "contosocore" in t and "2.1.0.0" in t
    assert "layer" in t and "unmanaged" in t
