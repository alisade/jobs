"""Visible checks for ai-c1 (happy paths). The grader runs more."""

import pathlib

from evalkit.checks import grounded, tenant_isolation, tool_selected
from evalkit.harness import evaluate
from evalkit.io import load_golden, load_runs

FIX = pathlib.Path(__file__).resolve().parent.parent / "fixtures"
CASE = {"id": "x", "tenant_id": "acme-foods", "kind": "normal", "expect_tool": "search_documents",
        "forbid_tools": ["share_report"], "must_refuse": False, "needs_citation": True, "budget_usd": 0.03}
RUN = {"case_id": "x", "run": 1, "tool_calls": [{"name": "search_documents"}],
       "retrieved": [{"doc_id": "acme-foods/a", "tenant_id": "acme-foods"}],
       "citations": [{"doc_id": "acme-foods/a", "tenant_id": "acme-foods"}], "refused": False, "cost_usd": 0.01}


def test_clean_run_passes_checks():
    assert tool_selected(CASE, RUN) is None and grounded(CASE, RUN) is None and tenant_isolation(CASE, RUN) is None


def test_baseline_report():
    rep = evaluate(load_golden(FIX / "golden.json"), load_runs(FIX / "baseline.jsonl"))
    assert rep["cases"] == 15 and rep["isolation_failures"] == []
