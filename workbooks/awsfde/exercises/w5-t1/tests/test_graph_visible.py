"""Visible checks for w5-t1. The grader runs more."""

from graph_tool.run import suppliers_of_product
from replay import build_graph


def test_acme_penne_suppliers(tmp_path):
    g, _ = build_graph(tmp_path)
    assert sorted(r[0] for r in suppliers_of_product(g, "acme-foods", "Penne 1kg")) == \
        ["Golden Grain Mills", "Pacific Packaging"]


def test_brightline_exam_kit_suppliers(tmp_path):
    g, _ = build_graph(tmp_path)
    assert sorted(r[0] for r in suppliers_of_product(g, "brightline-health", "Exam room kit")) == \
        ["Clearview Syringe Co", "Northwind Medical Gloves"]
