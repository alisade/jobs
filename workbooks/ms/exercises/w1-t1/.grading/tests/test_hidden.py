"""Hidden checks for ms/w1-t1: the fixed pipeline definition."""

import hashlib
import json
import os
import re
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _grader_sim import simulate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
PIPE = os.path.join(ROOT, "pipelines", "PL_Nightly_ERP_Load.DataPipeline", "pipeline-content.json")
DDL = os.path.join(ROOT, "warehouse", "WH_Control", "etl", "Tables", "load_control.sql")
DDL_SHA = "a256e11e1afbf00f249937204d75ef8de15e564454cdc7b53d7be39e67dfe86f"
ALLOWED_CONDITIONS = {"Succeeded", "Failed", "Skipped", "Completed"}


@pytest.fixture(scope="module")
def pipe():
    with open(PIPE) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def run():
    return simulate(PIPE, run_id="grader-run")


def acts(p):
    return {a["name"]: a for a in p["properties"]["activities"]}


def walk(acts_list, parent=None):
    for a in acts_list:
        yield a, parent
        inner = (a.get("typeProperties") or {}).get("activities")
        if inner:
            yield from walk(inner, a)


def expressions(obj):
    if isinstance(obj, dict):
        if obj.get("type") == "Expression" and isinstance(obj.get("value"), str):
            yield obj["value"]
        for v in obj.values():
            yield from expressions(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from expressions(v)


def lookup_columns(p):
    q = acts(p)["LookupTables"]["typeProperties"]["source"]["sqlReaderQuery"]["value"]
    cols = re.match(r"(?is)\s*select\s+(.*?)\s+from", q).group(1)
    return [c.strip().strip("[]") for c in cols.split(",")]


def test_lookup_returns_all_rows(pipe):
    tp = acts(pipe)["LookupTables"]["typeProperties"]
    assert tp.get("firstRowOnly", True) is False, "LookupTables must return all rows (firstRowOnly false)"


def test_foreach_items_bound_to_lookup_value(pipe):
    items = acts(pipe)["ForEachTable"]["typeProperties"]["items"]
    assert items.get("type") == "Expression"
    assert re.fullmatch(r"@activity\('LookupTables'\)\.output\.value", items["value"].strip()), items["value"]


def test_item_properties_exist_in_lookup_select(pipe):
    cols = set(lookup_columns(pipe))
    used = set()
    for e in expressions(acts(pipe)["ForEachTable"]):
        used |= set(re.findall(r"item\(\)\.([A-Za-z_][A-Za-z0-9_]*)", e))
    missing = used - cols
    assert used, "ForEach inner activities should use item() properties"
    assert not missing, f"item() properties not returned by the Lookup query: {sorted(missing)}"


def test_control_table_ddl_not_changed():
    with open(DDL, "rb") as f:
        assert hashlib.sha256(f.read()).hexdigest() == DDL_SHA, "fix the pipeline, not the deployed warehouse schema"


def test_activity_references_are_declared_and_upstream(pipe):
    top = pipe["properties"]["activities"]
    all_names = {a["name"] for a, _ in walk(top)}

    def upstream(a, scope):
        by = {x["name"]: x for x in scope}
        seen, stack = set(), [d["activity"] for d in a.get("dependsOn") or []]
        while stack:
            n = stack.pop()
            if n in seen or n not in by:
                continue
            seen.add(n)
            stack += [d["activity"] for d in by[n].get("dependsOn") or []]
        return seen

    def check(scope, inherited):
        for a in scope:
            allowed = upstream(a, scope) | inherited
            refs = set()
            tp = dict(a.get("typeProperties") or {})
            tp.pop("activities", None)
            for e in expressions(tp):
                refs |= set(re.findall(r"activity\('([^']+)'\)", e))
            assert refs <= all_names, f"{a['name']} references undefined activity {refs - all_names}"
            assert refs <= allowed, f"{a['name']} references activity that is not upstream: {refs - allowed}"
            inner = (a.get("typeProperties") or {}).get("activities")
            if inner:
                check(inner, allowed)

    check(top, set())


def test_pipeline_parameters_used_are_declared(pipe):
    declared = set((pipe["properties"].get("parameters") or {}).keys())
    used = set()
    for e in expressions(pipe):
        used |= set(re.findall(r"pipeline\(\)\.parameters\.([A-Za-z_][A-Za-z0-9_]*)", e))
    assert used <= declared, f"undeclared parameters: {used - declared}"


def test_dependency_graph_is_valid(pipe):
    for a, _ in walk(pipe["properties"]["activities"]):
        for d in a.get("dependsOn") or []:
            assert set(d["dependencyConditions"]) <= ALLOWED_CONDITIONS
    a = acts(pipe)
    assert {"activity": "LookupTables", "dependencyConditions": ["Succeeded"]} in a["ForEachTable"]["dependsOn"]
    fail_deps = a["FailWithContext"]["dependsOn"]
    assert any(d["activity"] == "ForEachTable" and "Failed" in d["dependencyConditions"] for d in fail_deps)
    inner = {x["name"]: x for x in a["ForEachTable"]["typeProperties"]["activities"]}
    assert inner["UpdateWatermark"]["dependsOn"] == [{"activity": "CopyTable", "dependencyConditions": ["Succeeded"]}], \
        "the watermark may only move after a successful copy"


def _timespan_seconds(ts):
    m = re.fullmatch(r"(?:(\d+)\.)?(\d{1,2}):(\d{2}):(\d{2})", ts)
    assert m, f"bad timespan {ts}"
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + s


def test_policies_are_sane(pipe):
    for a, _ in walk(pipe["properties"]["activities"]):
        if a["type"] in ("Lookup", "Copy", "Script"):
            pol = a.get("policy") or {}
            assert 1 <= int(pol.get("retry", 0)) <= 5, f"{a['name']}: retry should be 1-5"
            assert _timespan_seconds(pol.get("timeout", "7.00:00:00")) <= 12 * 3600, f"{a['name']}: timeout above 12h"


def test_foreach_parallel_settings(pipe):
    tp = acts(pipe)["ForEachTable"]["typeProperties"]
    assert tp.get("isSequential") is False
    assert 1 <= int(tp.get("batchCount", 20)) <= 50


def test_dry_run_succeeds(run):
    assert run["status"] == "Succeeded", [r["error"] for r in run["activityRuns"] if r["status"] == "Failed"][:1]


def test_dry_run_copies_exactly_the_enabled_erp_tables(run):
    copies = [r for r in run["activityRuns"] if r["activityType"] == "Copy" and r["status"] == "Succeeded"]
    queries = sorted(r["output"]["sourceQuery"] for r in copies)
    assert len(copies) == 4
    for schema, table in [("Sales", "SalesOrderHeader"), ("Sales", "SalesOrderLine"),
                          ("Purchasing", "PurchaseOrderHeader"), ("Production", "Product")]:
        assert any(f"[{schema}].[{table}]" in q and "[ModifiedDate] > '2026-10-11T02:00:00.000'" in q for q in queries), (schema, table, queries)
    assert sorted(r["output"]["sinkTable"] for r in copies) == sorted(
        ["erp_sales_order_header", "erp_sales_order_line", "erp_purchase_order_header", "erp_product"])
    assert not any("CustomerArchive" in q or "Account" in q for q in queries)


def test_dry_run_updates_each_watermark_once(run):
    scripts = [r for r in run["activityRuns"] if r["activityName"] == "UpdateWatermark" and r["status"] == "Succeeded"]
    ids = sorted(int(re.search(r"load_id = (\d+)", r["input"]["scripts"][0]["text"]).group(1)) for r in scripts)
    assert ids == [1, 2, 3, 4]


def test_answer_names_the_root_cause():
    with open(os.path.join(ROOT, "ANSWER.md")) as f:
        text = f.read().lower()
    assert "firstrowonly" in text.replace(" ", "") or "first row only" in text
    assert "firstrow" in text.replace(" ", "")
