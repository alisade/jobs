"""Visible tests on the committed prompt-v3 data. Run: make test"""

from __future__ import annotations

import pytest

from evalkit import metrics as m
from evalkit.report import build_report, gate


def test_overall_accuracy(labels, runs):
    assert m.accuracy(labels, runs, "overall") == pytest.approx(143 / 149)


def test_overall_exception_recall(labels, runs):
    s = m.exception_scores(labels, runs, "overall")
    assert (s["tp"], s["fn"], s["fp"]) == (29, 1, 0)
    assert s["recall"] == pytest.approx(29 / 30)


def test_report_and_gate_pass_on_v3(labels, runs, prices, baseline):
    r = build_report(labels, runs, prices)
    assert r["missing_runs"] == [{"sample_id": "S017", "run": 5}]
    assert gate(r, baseline["metrics"], baseline["thresholds"]) == []
