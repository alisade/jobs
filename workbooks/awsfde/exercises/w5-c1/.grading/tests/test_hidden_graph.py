"""Hidden checks for w5-c1: query results, tenant isolation with planted cross-tenant edges, the tool."""

from __future__ import annotations

import pytest
from w5c1_hidden_support import GRAPH_ID, payload, q

from graphlib.cypher import read_query
from graphlib.graph_tool import (MAX_ROWS, QUERY_TIMEOUT_MS, TEMPLATES, CallerContext, ToolError,
                                 build_request, check_tenant_scoped, run_tool)

ACME = CallerContext("acme-foods", "u-7f3a", "req-1")
NAMES = ["q1_suppliers_of_product", "q2_customers_exposed_to_supplier", "q3_products_within_two_hops",
         "q4_parts_per_supplier", "q5_suppliers_in_country"]


def poison(g):
    """Bad data: cross-tenant relationships that must never surface in a tenant's answer."""
    g.add_node("corvid-logistics:cust-02", __labels__={"Customer"}, name="Interstate Haulers", tenant_id="corvid-logistics")
    g.add_edge("corvid-logistics:sup-01", "acme-foods:part-03", __labels__={"SUPPLIES"}, rel_id="x1")
    g.add_edge("corvid-logistics:cust-02", "acme-foods:prod-01", __labels__={"ORDERED"}, rel_id="x2")
    g.add_edge("acme-foods:part-01", "corvid-logistics:prod-01", __labels__={"USED_IN"}, rel_id="x3")
    g.add_edge("corvid-logistics:sup-02", "acme-foods:fac-02", __labels__={"LOCATED_IN"}, rel_id="x4")
    return g


@pytest.mark.parametrize("product,want", [
    ("Penne 1kg", [("Golden Grain Mills",), ("Pacific Packaging",)]),
    ("Fresh pasta kit", [("ColdBox Containers",), ("Golden Grain Mills",), ("Pacific Packaging",)]),
])
def test_q1(graph, product, want):
    assert q(NAMES[0], graph, tenant_id="acme-foods", product=product) == want


def test_q2_both_tenants(graph):
    assert q(NAMES[1], graph, tenant_id="acme-foods", supplier="Pacific Packaging") == \
        [("Hillside Markets",), ("Maple Row Deli Co-op",), ("Northgate Grocers",)]
    assert q(NAMES[1], graph, tenant_id="corvid-logistics", supplier="Pacific Packaging") == [("Hillside Markets",)]
    assert q(NAMES[1], graph, tenant_id="acme-foods", supplier="Golden Grain Mills") == \
        [("Maple Row Deli Co-op",), ("Northgate Grocers",)]


def test_q3_variable_length(graph):
    assert q(NAMES[2], graph, tenant_id="acme-foods", supplier="Golden Grain Mills") == [("Fresh pasta kit",), ("Penne 1kg",)]
    assert q(NAMES[2], graph, tenant_id="acme-foods", supplier="ColdBox Containers") == [("Fresh pasta kit",)]
    assert "*" in read_query(NAMES[2]), "q3 must use a variable-length relationship"


def test_q4_other_tenant(graph):
    assert sorted(q(NAMES[3], graph, tenant_id="corvid-logistics")) == [("Pacific Packaging", 1), ("Ridge Tire Supply", 1)]


@pytest.mark.parametrize("country,want", [("US", [("Golden Grain Mills",), ("Sierra Farms",)]),
                                          ("MX", [("Pacific Packaging",)]), ("CA", [("ColdBox Containers",)])])
def test_q5(graph, country, want):
    assert q(NAMES[4], graph, tenant_id="acme-foods", country=country) == want


def test_isolation_with_planted_cross_tenant_edges(graph):
    g = poison(graph)
    assert q(NAMES[0], g, tenant_id="acme-foods", product="Marinara 680g") == [("Pacific Packaging",), ("Sierra Farms",)]
    assert ("Interstate Haulers",) not in q(NAMES[1], g, tenant_id="acme-foods", supplier="Golden Grain Mills")
    assert q(NAMES[2], g, tenant_id="acme-foods", supplier="Golden Grain Mills") == [("Fresh pasta kit",), ("Penne 1kg",)]
    assert sorted(q(NAMES[3], g, tenant_id="corvid-logistics")) == [("Pacific Packaging", 1), ("Ridge Tire Supply", 1)]
    assert q(NAMES[4], g, tenant_id="acme-foods", country="MX") == [("Pacific Packaging",)]
    assert q(NAMES[4], g, tenant_id="corvid-logistics", country="MX") == []


@pytest.mark.parametrize("name", NAMES)
def test_learner_queries_are_tenant_scoped(name):
    check_tenant_scoped(read_query(name))


@pytest.mark.parametrize("bad", [
    "MATCH (s:Supplier {tenant_id: $tenant_id})-[:SUPPLIES]->(p:Part) RETURN s.name",
    "MATCH (s:Supplier)-[:SUPPLIES]->(p:Part) WHERE s.tenant_id = $tenant_id RETURN p.name",
    "MATCH (s:Supplier {tenant_id: $tenant_id})-[:SUPPLIES]->()-[:USED_IN]->(x:Product {tenant_id: $tenant_id}) RETURN x.name",
    "MATCH (s:Supplier {tenant_id: 'acme-foods'}) RETURN s.name",
])
def test_checker_rejects_unscoped(bad):
    with pytest.raises(ValueError):
        check_tenant_scoped(bad)


def test_checker_accepts_where_form():
    check_tenant_scoped("MATCH (s:Supplier)-[:SUPPLIES]->(p:Part {tenant_id: $tenant_id}) "
                        "WHERE s.tenant_id = $tenant_id RETURN s.name")


@pytest.mark.parametrize("tool,args", [
    ("run_cypher", {"query": "MATCH (n) RETURN n"}),
    ("suppliers_of_product", {"product": "Penne 1kg", "query": "MATCH (n) DETACH DELETE n"}),
    ("suppliers_of_product", {"product": "Penne 1kg", "tenant_id": "corvid-logistics"}),
    ("suppliers_of_product", {}),
    ("suppliers_of_product", {"product": 42}),
    ("suppliers_of_product", {"product": "x" * 101}),
    ("suppliers_in_country", {"country": "usa"}),
    ("parts_per_supplier", {"supplier": "Sierra Farms"}),
])
def test_tool_rejects_bad_calls(tool, args):
    with pytest.raises(ToolError):
        build_request(GRAPH_ID, ACME, tool, args)


def test_tool_request_shape():
    req = build_request(GRAPH_ID, CallerContext("corvid-logistics", "u", "r"), "suppliers_in_country", {"country": "US"})
    assert req["graphIdentifier"] == GRAPH_ID and req["language"] == "OPEN_CYPHER"
    assert req["parameters"] == {"country": "US", "tenant_id": "corvid-logistics"}
    assert req["queryTimeoutMilliseconds"] == QUERY_TIMEOUT_MS and 0 < QUERY_TIMEOUT_MS <= 30000
    assert req["queryString"] == read_query(TEMPLATES["suppliers_in_country"]["query"])


def test_tool_truncates_and_sends_valid_request(neptune):
    rows = [{"s.name": f"S{i}"} for i in range(MAX_ROWS + 7)]
    neptune.stub.add_response("execute_query", payload(rows))
    out = run_tool(neptune.client, GRAPH_ID, ACME, "parts_per_supplier", {})
    assert len(out["rows"]) == MAX_ROWS and out["truncated"] is True
    assert neptune.requests[0]["parameters"] == {"tenant_id": "acme-foods"}
