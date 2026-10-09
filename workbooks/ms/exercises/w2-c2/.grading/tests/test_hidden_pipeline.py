import json
import pathlib
import re

import pytest

import pipecheck as pc

EX = pathlib.Path(__file__).resolve().parents[2]
PATH = EX / "pl_nightly_orchestrator.DataPipeline" / "pipeline-content.json"
NOTEBOOK_ID = "6c1f0e2a-4b7d-4c55-9a0e-2f8d3b1e7a10"
WORKSPACE_ID = "0b5e9d2c-71aa-4f3e-8c6b-5d2a9e4f1c33"
CHILD_ID = "a3d7c9e1-2f4b-4e8a-b1c6-7e9f0d2a5b48"


@pytest.fixture(scope="module")
def doc():
    return json.loads(PATH.read_text())


@pytest.fixture(scope="module")
def acts(doc):
    return {a["name"]: a for a, _ in pc.all_activities(doc["properties"]["activities"])}


def top(doc):
    return {a["name"]: a for a in doc["properties"]["activities"]}


def deps(a):
    return {(d["activity"], tuple(d["dependencyConditions"])) for d in a.get("dependsOn", [])}


def e(v):
    return pc.expr_text(v) or ""


def test_lint_clean(doc):
    assert pc.lint(doc) == []


def test_no_todo_left():
    assert "TODO" not in PATH.read_text()


def test_parameters(doc):
    p = doc["properties"]["parameters"]
    assert p["load_date"]["type"] == "String" and p["env"]["type"] == "String"
    assert p["regions"]["type"] == "Array"
    assert p["regions"].get("defaultValue") == ["east", "west", "central"]


def test_variable(doc):
    v = doc["properties"]["variables"]
    assert v.get("export_status", {}).get("type") == "String"


def test_notebook_activity(acts):
    nb = acts["nb_stage_orders"]
    assert nb["type"] == "TridentNotebook"
    tp = nb["typeProperties"]
    assert tp["notebookId"] == NOTEBOOK_ID and tp["workspaceId"] == WORKSPACE_ID
    params = tp.get("parameters") or {}
    for name in ("load_date", "env"):
        assert name in params, f"notebook base parameter {name} missing"
        assert params[name].get("type") == "string"
        assert re.fullmatch(rf"@pipeline\(\)\.parameters\.{name}", e(params[name].get("value")).strip())


def test_notebook_policy(acts):
    pol = acts["nb_stage_orders"].get("policy") or {}
    assert pc.timeout_seconds(pol.get("timeout")) == 2 * 3600
    assert pol.get("retry") == 2 and pol.get("retryIntervalInSeconds") == 120


def test_start_export(acts):
    w = acts["web_start_export"]
    tp = w["typeProperties"]
    assert w["type"] == "WebActivity" and tp["method"].upper() == "POST"
    body = e(tp.get("body"))
    assert "pipeline().parameters.load_date" in body and "pipeline().RunId" in body
    pol = w.get("policy") or {}
    assert pol.get("retry") == 3 and pol.get("retryIntervalInSeconds") == 30
    t = pc.timeout_seconds(pol.get("timeout"))
    assert t is not None and t <= 600, "a POST that hangs should not block the run for 12 hours"


def test_until_terminates(acts):
    u = acts["until_export_done"]
    tp = u["typeProperties"]
    t = pc.timeout_seconds(tp.get("timeout"))
    assert t is not None and 0 < t <= 3600, "Until timeout must be set and at most 1 hour"
    ex = e(tp["expression"]).replace(" ", "")
    assert "variables('export_status')" in ex
    assert "'Completed'" in ex and "'Failed'" in ex, "loop must stop on both terminal states"
    assert ex.startswith("@or("), "terminate on Completed OR Failed"


def test_until_inner_chain(acts):
    inner = {a["name"]: a for a in acts["until_export_done"]["typeProperties"]["activities"]}
    get = inner.get("web_get_export_status")
    assert get and get["typeProperties"]["method"].upper() == "GET"
    assert "activity('web_start_export').output.exportId" in e(get["typeProperties"].get("relativeUrl")) + e(get["typeProperties"].get("url"))
    sets = [a for a in inner.values() if a["type"] == "SetVariable"]
    assert len(sets) == 1
    s = sets[0]
    assert s["typeProperties"]["variableName"] == "export_status"
    assert "activity('web_get_export_status').output.status" in e(s["typeProperties"]["value"])
    assert ("web_get_export_status", ("Succeeded",)) in deps(s)
    waits = [a for a in inner.values() if a["type"] == "Wait"]
    assert len(waits) == 1
    secs = waits[0]["typeProperties"]["waitTimeInSeconds"]
    assert isinstance(secs, int) and 30 <= secs <= 300, "poll every 30-300 seconds"
    assert (s["name"], ("Succeeded",)) in deps(waits[0]), "wait after recording the status"


def test_timeout_path(doc):
    t = top(doc)
    f = [a for a in t.values() if ("until_export_done", ("Failed",)) in deps(a)]
    assert len(f) == 1 and f[0]["type"] == "Fail", "an Until timeout surfaces as Failed: handle it"
    assert f[0]["typeProperties"]["errorCode"] == "EXPORT_TIMEOUT"


def test_if_export_failed(doc):
    i = top(doc)["if_export_failed"]
    assert i["type"] == "IfCondition"
    assert ("until_export_done", ("Succeeded",)) in deps(i)
    assert e(i["typeProperties"]["expression"]).replace(" ", "") == "@equals(variables('export_status'),'Failed')"
    tru = i["typeProperties"]["ifTrueActivities"]
    assert len(tru) == 1 and tru[0]["type"] == "Fail" and tru[0]["typeProperties"]["errorCode"] == "EXPORT_FAILED"


def test_foreach(doc, acts):
    f = top(doc)["foreach_region"]
    tp = f["typeProperties"]
    assert ("if_export_failed", ("Succeeded",)) in deps(f)
    assert tp.get("isSequential") is False and tp.get("batchCount") == 3
    assert e(tp["items"]).strip() == "@pipeline().parameters.regions"
    inner = tp["activities"]
    assert len(inner) == 1
    inv = inner[0]
    assert inv["type"] in ("InvokePipeline", "ExecutePipeline")
    itp = inv["typeProperties"]
    assert itp.get("waitOnCompletion") is True, "without waitOnCompletion child failures never reach the parent"
    if inv["type"] == "InvokePipeline":
        assert itp.get("pipelineId") == CHILD_ID and itp.get("workspaceId") == WORKSPACE_ID
    else:
        assert itp["pipeline"]["referenceName"] == CHILD_ID
    p = itp.get("parameters") or {}
    assert e(p.get("region")).strip() == "@item()"
    assert "pipeline().parameters.load_date" in e(p.get("load_date"))


@pytest.mark.parametrize("name,src,code", [
    ("fail_staging", "nb_stage_orders", "STAGING_FAILED"),
    ("fail_region_loads", "foreach_region", "REGION_LOAD_FAILED"),
])
def test_failure_branches(doc, name, src, code):
    a = top(doc).get(name)
    assert a and a["type"] == "Fail"
    assert deps(a) == {(src, ("Failed",))}
    assert a["typeProperties"]["errorCode"] == code


def test_fail_messages_carry_run_id(acts):
    fails = [a for a in acts.values() if a["type"] == "Fail"]
    assert len(fails) >= 4
    for f in fails:
        assert "pipeline().RunId" in e(f["typeProperties"]["message"]), f"{f['name']}: include the run id"


def test_happy_path_has_no_failed_dependency(doc):
    t = top(doc)
    for n in ("web_start_export", "until_export_done", "if_export_failed", "foreach_region"):
        assert all(c == ("Succeeded",) for _, c in deps(t[n])), f"{n} must only run on success"
