"""Visible tests: the harness still loads and scores. Run: make test"""

from __future__ import annotations

from harness.golden import load_golden, load_runs
from harness.score import score

from conftest import ROOT


def test_golden_loads_with_schema_v2():
    g = load_golden(ROOT / "labels" / "golden.jsonl")
    assert len(g) == 30 and all(r["control_id"] == "CM-03" for r in g.values())


def test_dashboard_scores_q3():
    s = score(load_golden(ROOT / "labels" / "golden.jsonl"), load_runs(ROOT / "runs" / "2026Q3" / "production.jsonl"))
    assert s["samples"] == 30


def test_reviewer_count_of_exceptions_is_reflected():
    # the reviewer re-performed all 30 items and found 7 exceptions
    s = score(load_golden(ROOT / "labels" / "golden.jsonl"), load_runs(ROOT / "runs" / "2026Q3" / "production.jsonl"))
    assert s["exceptions_in_golden"] == 7
