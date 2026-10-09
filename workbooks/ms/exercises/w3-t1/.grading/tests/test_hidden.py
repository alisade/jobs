"""Hidden tests for ms/w3-t1. Uses a private copy of the renderer and targets so edits to
deploy/render.py or deploy/targets.json cannot change the verdict."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import _render_ref as R  # noqa: E402

TARGETS = json.loads((HERE / "targets_ref.json").read_text())
GUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def env_guids(env):
    t = TARGETS[env]
    s = {t["workspace_id"]}
    for items in t["items"].values():
        s.update(items.values())
    return s


def meta(nb_path):
    lines, started = [], False
    for line in Path(nb_path).read_text().splitlines():
        if line == "# META" or line.startswith("# META "):
            started = True
            lines.append(line[6:].lstrip(" "))
        elif started:
            break
    return json.loads("\n".join(lines))["dependencies"]["lakehouse"]


def render_env(env, tmp_path, workspace=None):
    out = tmp_path / f"r-{env}"
    R.render(workspace or (ROOT / "workspace"), env, TARGETS, out)
    return out


def all_text(d):
    for f in sorted(Path(d).rglob("*")):
        if f.is_file() and f.name != ".platform":
            yield f, f.read_text()


@pytest.mark.parametrize("env", ["PROD", "PPE"])
def test_no_foreign_guid_after_render(env, tmp_path):
    out = render_env(env, tmp_path)
    foreign = set().union(*(env_guids(e) for e in TARGETS if not e.startswith("_") and e != env))
    hits = []
    for f, text in all_text(out):
        for g in GUID.findall(text):
            if g.lower() in foreign:
                hits.append(f"{f.relative_to(out)}: {g}")
    assert not hits, f"{env} render still references other environments: {hits[:5]}"


@pytest.mark.parametrize("env", ["PROD", "PPE"])
def test_gold_notebook_fully_bound(env, tmp_path):
    out = render_env(env, tmp_path)
    b = meta(out / "Load Gold Sales.Notebook" / "notebook-content.py")
    t = TARGETS[env]
    assert b["default_lakehouse"] == t["items"]["Lakehouse"]["lh_gold"]
    assert b["default_lakehouse_workspace_id"] == t["workspace_id"]
    assert sorted(k["id"] for k in b["known_lakehouses"]) == sorted(
        [t["items"]["Lakehouse"]["lh_gold"], t["items"]["Lakehouse"]["lh_silver"]]
    )


def test_silver_and_pipeline_not_regressed(tmp_path):
    out = render_env("PROD", tmp_path)
    t = TARGETS["PROD"]
    b = meta(out / "nb_load_silver.Notebook" / "notebook-content.py")
    assert b["default_lakehouse"] == t["items"]["Lakehouse"]["lh_silver"]
    doc = json.loads((out / "Daily Sales.DataPipeline" / "pipeline-content.json").read_text())
    acts = {a["name"]: a["typeProperties"] for a in doc["properties"]["activities"]}
    assert acts["Load Silver"]["notebookId"] == t["items"]["Notebook"]["nb_load_silver"]
    assert acts["Load Gold"]["notebookId"] == t["items"]["Notebook"]["Load Gold Sales"]
    assert {a["workspaceId"] for a in acts.values()} == {t["workspace_id"]}


def test_source_stays_dev_and_has_no_hardcoded_targets():
    """Fix belongs in parameterization, not in the git source: DEV must keep working."""
    ws = ROOT / "workspace"
    targets_guids = env_guids("PROD") | env_guids("PPE")
    for f, text in all_text(ws):
        for g in GUID.findall(text):
            assert g.lower() not in targets_guids, f"{f.relative_to(ws)} hardcodes a PPE/PROD id {g}"
    b = meta(ws / "Load Gold Sales.Notebook" / "notebook-content.py")
    assert b["default_lakehouse_workspace_id"] == TARGETS["DEV"]["workspace_id"]
    assert b["default_lakehouse"] == TARGETS["DEV"]["items"]["Lakehouse"]["lh_gold"]


def test_dev_render_is_noop(tmp_path):
    """DEV is not a key in replace_value: rendering for DEV must leave definitions untouched."""
    out = render_env("DEV", tmp_path)
    ws = ROOT / "workspace"
    for f, text in all_text(ws):
        if f.name == "parameter.yml":
            continue
        assert (out / f.relative_to(ws)).read_text() == text


def test_fix_survives_the_next_rename(tmp_path):
    """Rename the gold notebook again (display name + folder). PROD must still bind to PROD."""
    ws = tmp_path / "ws"
    shutil.copytree(ROOT / "workspace", ws)
    old = ws / "Load Gold Sales.Notebook"
    new = ws / "Gold - Daily Sales.Notebook"
    old.rename(new)
    plat = json.loads((new / ".platform").read_text())
    plat["metadata"]["displayName"] = "Gold - Daily Sales"
    (new / ".platform").write_text(json.dumps(plat, indent=2))
    # The pipeline entry would need the new name too; drop pipelines from this check.
    shutil.rmtree(ws / "Daily Sales.DataPipeline")
    params = (ws / "parameter.yml").read_text()
    params = params.split("key_value_replace:")[0]
    (ws / "parameter.yml").write_text(params)
    out = tmp_path / "out"
    R.render(ws, "PROD", TARGETS, out)
    b = meta(out / "Gold - Daily Sales.Notebook" / "notebook-content.py")
    assert b["default_lakehouse_workspace_id"] == TARGETS["PROD"]["workspace_id"], (
        "binding depends on the notebook display name; the next rename will silently break PROD again"
    )


def test_parameter_entries_cover_both_targets():
    import yaml
    p = yaml.safe_load((ROOT / "workspace" / "parameter.yml").read_text())
    for section in ("find_replace", "key_value_replace"):
        for e in p.get(section) or []:
            keys = {k.lower() for k in e["replace_value"]}
            assert "_all_" in keys or {"ppe", "prod"} <= keys, f"{section} entry missing an environment: {e}"


# ---------- guard ----------

import check_bindings  # noqa: E402  (learner's deploy/check_bindings.py via pythonpath)


def test_guard_reports_starter_style_leak(tmp_path):
    d = tmp_path / "Load Gold Sales.Notebook"
    d.mkdir()
    dev_lh = TARGETS["DEV"]["items"]["Lakehouse"]["lh_gold"]
    (d / "notebook-content.py").write_text(f'# META       "default_lakehouse": "{dev_lh}",\n')
    leaks = check_bindings.find_leaks(tmp_path, "PROD", TARGETS)
    assert len(leaks) == 1
    assert dev_lh in leaks[0] and "notebook-content.py" in leaks[0] and "DEV" in leaks[0]


def test_guard_flags_ppe_guid_in_prod(tmp_path):
    d = tmp_path / "Daily Sales.DataPipeline"
    d.mkdir()
    ppe_ws = TARGETS["PPE"]["workspace_id"].upper()
    (d / "pipeline-content.json").write_text(json.dumps({"workspaceId": ppe_ws}))
    leaks = check_bindings.find_leaks(tmp_path, "PROD", TARGETS)
    assert leaks and "PPE" in leaks[0], "case-insensitive GUID match and cross-target (PPE in PROD) detection"


def test_guard_clean_render_and_unknown_guids(tmp_path):
    out = render_env("PROD", tmp_path)
    (out / "notes.txt").write_text("random id 11111111-2222-4333-8444-555555555555 is not ours\n")
    assert check_bindings.find_leaks(out, "PROD", TARGETS) == []


def test_guard_ignores_platform_files(tmp_path):
    d = tmp_path / "X.Notebook"
    d.mkdir()
    (d / ".platform").write_text(json.dumps({"config": {"logicalId": TARGETS["DEV"]["workspace_id"]}}))
    assert check_bindings.find_leaks(tmp_path, "PROD", TARGETS) == []


def test_guard_cli_exit_codes(tmp_path):
    bad = tmp_path / "bad" / "X.Notebook"
    bad.mkdir(parents=True)
    (bad / "notebook-content.py").write_text(TARGETS["DEV"]["workspace_id"])
    tf = tmp_path / "t.json"
    tf.write_text(json.dumps(TARGETS))
    cmd = [sys.executable, str(ROOT / "deploy" / "check_bindings.py"), "--env", "PROD", "--targets", str(tf)]
    r1 = subprocess.run(cmd + ["--rendered", str(tmp_path / "bad")], capture_output=True, text=True, timeout=60)
    assert r1.returncode == 1 and "LEAK" in r1.stdout
    good = render_env("PROD", tmp_path)
    r2 = subprocess.run(cmd + ["--rendered", str(good)], capture_output=True, text=True, timeout=60)
    assert r2.returncode == 0, r2.stdout + r2.stderr


def test_answer_names_the_silent_filter_skip():
    text = (ROOT / "ANSWER.md").read_text().lower()
    assert "item_name" in text and ("skip" in text or "silent" in text), (
        "ANSWER.md should explain the item_name filter no longer matching after the rename"
    )
