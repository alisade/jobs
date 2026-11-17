"""Visible checks for w5-c1 (happy paths). The grader runs more."""

from w5c1_support import GRAPH_ID, payload, q

from graphlib.graph_tool import CallerContext, build_request, run_tool

CTX = CallerContext("acme-foods", "u-7f3a", "req-1")


def test_q1_suppliers_of_marinara(graph):
    assert q("q1_suppliers_of_product", graph, tenant_id="acme-foods", product="Marinara 680g") == \
        [("Pacific Packaging",), ("Sierra Farms",)]


def test_q4_parts_per_supplier(graph):
    assert sorted(q("q4_parts_per_supplier", graph, tenant_id="acme-foods")) == \
        [("ColdBox Containers", 1), ("Golden Grain Mills", 1), ("Pacific Packaging", 3), ("Sierra Farms", 1)]


def test_tool_binds_tenant_from_context():
    req = build_request(GRAPH_ID, CTX, "suppliers_of_product", {"product": "Penne 1kg"})
    assert req["parameters"] == {"product": "Penne 1kg", "tenant_id": "acme-foods"}
    assert req["language"] == "OPEN_CYPHER"


def test_tool_runs(neptune):
    neptune.stub.add_response("execute_query", payload([{"s.name": "Golden Grain Mills"}]))
    out = run_tool(neptune.client, GRAPH_ID, CTX, "suppliers_of_product", {"product": "Penne 1kg"})
    assert out == {"rows": [{"s.name": "Golden Grain Mills"}], "truncated": False}
