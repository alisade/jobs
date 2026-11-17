"""Visible tests: render PROD and check the notebooks bind to PROD."""

import json

from conftest import binding

import render
import check_bindings


def _render(root, targets, env, tmp_path):
    out = tmp_path / env
    render.render(root / "workspace", env, targets, out)
    return out


def test_silver_notebook_binds_to_prod(root, targets, tmp_path):
    out = _render(root, targets, "PROD", tmp_path)
    b = binding(out / "nb_load_silver.Notebook" / "notebook-content.py")
    assert b["default_lakehouse"] == targets["PROD"]["items"]["Lakehouse"]["lh_silver"]
    assert b["default_lakehouse_workspace_id"] == targets["PROD"]["workspace_id"]


def test_gold_notebook_binds_to_prod(root, targets, tmp_path):
    out = _render(root, targets, "PROD", tmp_path)
    b = binding(out / "Load Gold Sales.Notebook" / "notebook-content.py")
    assert b["default_lakehouse_workspace_id"] == targets["PROD"]["workspace_id"], "gold notebook still bound to another workspace"
    assert b["default_lakehouse"] == targets["PROD"]["items"]["Lakehouse"]["lh_gold"]


def test_pipeline_points_at_prod_notebooks(root, targets, tmp_path):
    out = _render(root, targets, "PROD", tmp_path)
    doc = json.loads((out / "Daily Sales.DataPipeline" / "pipeline-content.json").read_text())
    acts = {a["name"]: a["typeProperties"] for a in doc["properties"]["activities"]}
    assert acts["Load Gold"]["notebookId"] == targets["PROD"]["items"]["Notebook"]["Load Gold Sales"]
    assert acts["Load Gold"]["workspaceId"] == targets["PROD"]["workspace_id"]


def test_guard_flags_a_dev_guid(targets, tmp_path):
    d = tmp_path / "rendered" / "X.Notebook"
    d.mkdir(parents=True)
    (d / "notebook-content.py").write_text('# META "default_lakehouse_workspace_id": "%s"\n' % targets["DEV"]["workspace_id"])
    leaks = check_bindings.find_leaks(tmp_path / "rendered", "PROD", targets)
    assert leaks and targets["DEV"]["workspace_id"] in leaks[0]
