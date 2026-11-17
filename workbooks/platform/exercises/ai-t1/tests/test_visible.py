"""Visible tests for ai-t1."""
from pathlib import Path

from agent import pipeline

PLAN = Path(__file__).resolve().parents[1] / "evidence" / "plan-run-212.json"


def test_dirty_plan_does_not_open_a_pr():
    res = pipeline.run(PLAN)
    assert res["pr_opened"] is False
    assert res["verdict"].counts["replace"] == 1
