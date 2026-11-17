"""Hidden tests for audit/w6-c1: metric definitions on hand-computed data, edge cases, CLI gate."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from evalkit import metrics as m
from evalkit.data import load_runs
from evalkit.report import build_report, gate, to_markdown

ROOT = Path(__file__).resolve().parents[1]
PRICES = {"per_1m_usd": {"input": 0.30, "cached_input": 0.03, "output": 2.50}}


def lab(sid, overall, **attrs):
    labels = {a: "pass" for a in m.ATTRIBUTES}
    labels.update(attrs)
    return sid, {"sample_id": sid, "labels": labels, "overall": overall, "labeled_by": "human:x"}


def run(sid, k, overall, latency=1000, usage=None, **attrs):
    o = {a: "pass" for a in m.ATTRIBUTES}
    o.update(attrs)
    return {"sample_id": sid, "run": k, "outputs": o, "overall": overall, "latency_ms": latency,
            "usage": usage or {"prompt_tokens": 1000, "cached_tokens": 400, "output_tokens": 100}}


LABELS = dict([lab("L1", "exception", independent_approver="exception"), lab("L2", "pass"),
               lab("L3", "needs_review", tests_passed="not_evaluable")])
RUNS = [
    run("L1", 1, "exception", independent_approver="exception"), run("L1", 2, "exception", independent_approver="exception"), run("L1", 3, "pass"),
    run("L2", 1, "pass"), run("L2", 2, "pass"), run("L2", 3, "exception", linked_change="exception"),
    run("L3", 1, "needs_review", tests_passed="not_evaluable"), run("L3", 2, "pass"), run("L3", 3, "needs_review", tests_passed="not_evaluable"),
]


def test_accuracy_run_level():
    assert m.accuracy(LABELS, RUNS, "overall") == pytest.approx(6 / 9)
    assert m.accuracy(LABELS, RUNS, "tests_passed") == pytest.approx(8 / 9)


def test_accuracy_no_rows_is_none():
    assert m.accuracy(LABELS, [], "overall") is None


def test_exception_scores_hand_computed():
    s = m.exception_scores(LABELS, RUNS, "overall")
    assert (s["tp"], s["fp"], s["fn"], s["support"]) == (2, 1, 1, 3)
    assert s["recall"] == pytest.approx(2 / 3) and s["precision"] == pytest.approx(2 / 3)


def test_zero_exceptions_in_slice_is_none_not_zero():
    s = m.exception_scores(LABELS, [r for r in RUNS if r["sample_id"] != "L2"], "linked_change")
    assert s["support"] == 0 and s["recall"] is None and s["precision"] is None


def test_unlabeled_and_duplicate_rows_are_not_scored():
    extra = RUNS + [run("X9", 1, "pass"), dict(RUNS[2], overall="exception")]
    assert m.accuracy(LABELS, extra, "overall") == pytest.approx(6 / 9)
    rep = build_report(LABELS, extra, PRICES, expected_runs=3)
    assert rep["unlabeled_samples"] == ["X9"] and rep["runs_scored"] == 9


def test_modal_tie_break_prefers_severe():
    assert m.modal(["pass", "exception", "needs_review"]) == ("exception", 1)
    assert m.modal(["pass", "pass", "needs_review", "needs_review"]) == ("needs_review", 2)
    assert m.modal(["pass", "pass", "exception"]) == ("pass", 2)


def test_agreement_hand_computed():
    a = m.agreement(RUNS, "overall")
    assert a["mean_modal_agreement"] == pytest.approx(2 / 3)
    assert a["fully_consistent_share"] == 0 and a["samples"] == 3


def test_all_runs_disagree():
    rows = [run("D", 1, "pass"), run("D", 2, "exception"), run("D", 3, "needs_review")]
    assert m.agreement(rows)["mean_modal_agreement"] == pytest.approx(1 / 3)


def test_fleiss_kappa_hand_computed():
    k = m.fleiss_kappa(RUNS, "overall", 3)
    assert k["subjects"] == 3
    assert k["kappa"] == pytest.approx(-1 / 26)


def test_fleiss_kappa_perfect_and_textbook():
    perfect = [run(s, k, "pass") for s in ("A", "B") for k in (1, 2, 3)]
    assert m.fleiss_kappa(perfect, "overall", 3)["kappa"] == pytest.approx(1.0)
    rows = [run("A", 1, "pass"), run("A", 2, "pass"), run("B", 1, "exception"), run("B", 2, "exception")]
    assert m.fleiss_kappa(rows, "overall", 2)["kappa"] == pytest.approx(1.0)
    rows = [run("A", 1, "pass"), run("A", 2, "exception"), run("B", 1, "exception"), run("B", 2, "pass")]
    assert m.fleiss_kappa(rows, "overall", 2)["kappa"] == pytest.approx(-1.0)


def test_fleiss_kappa_skips_incomplete_subjects():
    rows = RUNS[:-1]  # L3 now has 2 of 3 runs
    k = m.fleiss_kappa(rows, "overall", 3)
    assert k["subjects"] == 2


def test_run_cost_discounts_cached_tokens():
    assert m.run_cost(RUNS[0], PRICES) == pytest.approx(442e-6)
    c = m.cost(RUNS, PRICES)
    assert c["total_usd"] == pytest.approx(9 * 442e-6) and c["per_100_samples_usd"] == pytest.approx(100 * 442e-6)
    assert c["runs"] == 9


def test_percentile_nearest_rank():
    vals = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    assert m.percentile(vals, 50) == 50 and m.percentile(vals, 95) == 100
    assert m.percentile([3, 1, 2], 50) == 2 and m.percentile([5], 95) == 5
    assert m.percentile([], 50) is None


def test_latency_report():
    rows = [run("L", k, "pass", latency=v) for k, v in enumerate([900, 100, 500, 300, 700], start=1)]
    assert m.latency(rows) == {"p50_ms": 500, "p95_ms": 900, "runs": 5}


def test_report_keys_and_missing_runs():
    rep = build_report(LABELS, RUNS[:-1], PRICES, expected_runs=3)
    for k in ("control", "samples", "runs_scored", "missing_runs", "unlabeled_samples", "accuracy", "exceptions", "consistency", "cost", "latency"):
        assert k in rep
    assert rep["missing_runs"] == [{"sample_id": "L3", "run": 3}]
    assert set(rep["accuracy"]) == set(m.FIELDS) and set(rep["exceptions"]) == set(m.FIELDS)
    assert set(rep["consistency"]) == {"agreement", "fleiss_kappa"}
    json.dumps(rep)
    assert "CM-03" in to_markdown(rep)


THRESH = {"min_exception_recall": 0.95, "max_accuracy_drop": 0.02}


def test_gate_recall_and_accuracy():
    rep = build_report(LABELS, RUNS, PRICES, expected_runs=3)
    f = gate(rep, {"accuracy_overall": 0.9}, THRESH)
    assert len(f) == 2 and any("recall" in x for x in f) and any("accuracy" in x for x in f)


def test_gate_accuracy_exactly_at_floor_passes():
    rows = [run("L1", 1, "exception", independent_approver="exception"), run("L2", 1, "pass")]
    rep = build_report(LABELS, rows, PRICES, expected_runs=1)
    assert gate(rep, {"accuracy_overall": 1.02}, THRESH) == []


def test_gate_fails_without_labeled_exceptions():
    labels = dict([lab("L2", "pass")])
    rep = build_report(labels, [run("L2", 1, "pass")], PRICES, expected_runs=1)
    assert gate(rep, {"accuracy_overall": 1.0}, THRESH)


def test_committed_data_metrics(labels, runs, prices):
    rep = build_report(labels, runs, prices)
    assert rep["consistency"]["fleiss_kappa"]["subjects"] == 29
    assert rep["consistency"]["fleiss_kappa"]["kappa"] == pytest.approx(0.81569, abs=1e-4)
    assert rep["consistency"]["agreement"]["mean_modal_agreement"] == pytest.approx(0.96)
    assert rep["cost"]["per_100_samples_usd"] == pytest.approx(0.0874272, rel=1e-4)
    assert rep["latency"]["p50_ms"] == 3203 and rep["latency"]["p95_ms"] == 8392
    assert rep["exceptions"]["independent_approver"]["recall"] == pytest.approx(14 / 15)


def _cli(tmp_path, runs_file):
    return subprocess.run([sys.executable, "-m", "evalkit.cli", "--runs", runs_file, "--out", str(tmp_path)],
                          cwd=ROOT, capture_output=True, text=True, timeout=60)


def test_cli_passes_v3_and_writes_files(tmp_path):
    p = _cli(tmp_path, "data/runs.jsonl")
    assert p.returncode == 0, p.stderr
    rep = json.loads((tmp_path / "report.json").read_text())
    assert rep["gate"]["passed"] is True and (tmp_path / "summary.md").exists()


def test_cli_blocks_prompt_v4(tmp_path):
    p = _cli(tmp_path, "data/runs_prompt_v4.jsonl")
    assert p.returncode == 1
    rep = json.loads((tmp_path / "report.json").read_text())
    assert rep["exceptions"]["overall"]["recall"] == pytest.approx(20 / 30)
