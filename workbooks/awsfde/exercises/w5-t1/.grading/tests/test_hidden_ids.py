"""Hidden checks for w5-t1: tenant-scoped ids, the load validator, a scoped DISTINCT query, guards."""

from __future__ import annotations

import csv
import pathlib

import networkx as nx
import pytest

from export_job.export import export_tenant, node_id
from export_job.validate import validate_load
from graph_tool.run import suppliers_of_product
from neptune_sim.loader import bulk_load
from replay import build_graph

TENANTS = ["acme-foods", "brightline-health"]


def ids(nodes, edges):
    with open(nodes, newline="") as fh:
        n = [r[":ID"] for r in csv.DictReader(fh)]
    with open(edges, newline="") as fh:
        e = [(r[":ID"], r[":START_ID"], r[":END_ID"]) for r in csv.DictReader(fh)]
    return n, e


def write(path: pathlib.Path, header: list[str], rows: list[list[str]]) -> pathlib.Path:
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    return path


def old_style(tmp, tenant, nodes, edges):
    n = write(tmp / f"{tenant}-n.csv", [":ID", ":LABEL", "name:String", "tenant_id:String"],
              [[i, lab, name, t] for i, lab, name, t in nodes])
    e = write(tmp / f"{tenant}-e.csv", [":ID", ":START_ID", ":END_ID", ":TYPE"], edges)
    return n, e


def test_node_id_is_tenant_scoped():
    assert node_id("acme-foods", "part", 100) != node_id("brightline-health", "part", 100)
    assert node_id("acme-foods", "part", 100).startswith("acme-foods")
    with pytest.raises(ValueError):
        node_id("", "part", 1)


def test_exported_ids_never_collide(tmp_path):
    seen = {}
    for t in TENANTS:
        n, e = ids(*export_tenant(t, tmp_path))
        for x in n + [r[0] for r in e]:
            assert x.startswith(t), x
            assert x not in seen, f"{x} exported by {seen.get(x)} and {t}"
            seen[x] = t
        for _, a, b in e:
            assert a.startswith(t) and b.startswith(t)


def test_validator_catches_id_collision(tmp_path):
    g = nx.MultiDiGraph()
    g.add_node("sup-001", __labels__={"Supplier"}, name="Golden Grain Mills", tenant_id="acme-foods")
    n, e = old_style(tmp_path, "brightline-health", [("sup-001", "Supplier", "Northwind", "brightline-health")], [])
    problems = validate_load("brightline-health", n, e, g)
    assert problems and any("sup-001" in p for p in problems)


def test_validator_catches_cross_tenant_edge(tmp_path):
    g = nx.MultiDiGraph()
    g.add_node("acme-foods:part-100", __labels__={"Part"}, name="Flour", tenant_id="acme-foods")
    n, e = old_style(tmp_path, "brightline-health",
                     [("brightline-health:sup-001", "Supplier", "Northwind", "brightline-health")],
                     [["brightline-health:e1", "brightline-health:sup-001", "acme-foods:part-100", "SUPPLIES"]])
    problems = validate_load("brightline-health", n, e, g)
    assert problems and any("acme-foods:part-100" in p for p in problems)


def test_validator_catches_duplicates_and_wrong_tenant_rows(tmp_path):
    n, e = old_style(tmp_path, "brightline-health",
                     [("brightline-health:sup-001", "Supplier", "A", "brightline-health"),
                      ("brightline-health:sup-001", "Supplier", "B", "brightline-health"),
                      ("brightline-health:sup-002", "Supplier", "C", "acme-foods")], [])
    assert len(validate_load("brightline-health", n, e, nx.MultiDiGraph())) >= 2


def test_validator_accepts_clean_loads_and_same_tenant_reload(tmp_path):
    g = nx.MultiDiGraph()
    for t in TENANTS:
        n, e = export_tenant(t, tmp_path)
        assert validate_load(t, n, e, g) == []
        bulk_load(g, n, e)
    n, e = export_tenant("acme-foods", tmp_path)
    assert validate_load("acme-foods", n, e, g) == []


def test_replay_loads_both_tenants_cleanly(tmp_path):
    _, jobs = build_graph(tmp_path)
    assert [j["status"] for j in jobs] == ["LOAD_COMPLETED", "LOAD_COMPLETED"]
    assert all(j["nodes_updated"] == 0 for j in jobs)


def test_query_only_returns_callers_tenant(tmp_path):
    g, _ = build_graph(tmp_path)
    for tenant, product in (("acme-foods", "Penne 1kg"), ("acme-foods", "Marinara 680g"),
                            ("brightline-health", "Exam room kit")):
        rows = suppliers_of_product(g, tenant, product)
        assert rows and all(r[1] == tenant for r in rows)


def test_query_scopes_every_node_against_bad_data(tmp_path):
    g, _ = build_graph(tmp_path)
    acme_part = next(n for n, d in g.nodes(data=True) if d.get("name") == "Durum wheat flour")
    bl_sup = next(n for n, d in g.nodes(data=True) if d.get("name") == "Northwind Medical Gloves")
    g.add_edge(bl_sup, acme_part, __labels__={"SUPPLIES"}, rel_id="bad-1")
    names = [r[0] for r in suppliers_of_product(g, "acme-foods", "Penne 1kg")]
    assert "Northwind Medical Gloves" not in names
    assert sorted(names) == ["Golden Grain Mills", "Pacific Packaging"]


def test_query_returns_each_supplier_once(tmp_path):
    g, _ = build_graph(tmp_path)
    assert sorted(r[0] for r in suppliers_of_product(g, "acme-foods", "Marinara 680g")) == ["Pacific Packaging", "Sierra Farms"]
