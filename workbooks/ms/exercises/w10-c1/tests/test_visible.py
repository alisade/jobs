"""Visible tests: the happy path on the recorded runs. Hidden tests cover edge cases."""
import json
from pathlib import Path

import pytest

from release_gate.evaluate import compare_runs, evaluate_run, gate, load_config, main
from release_gate.model import load_testset

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def cfg():
    return load_config(ROOT / "gate.yaml")


@pytest.fixture(scope="module")
def cases():
    return load_testset(ROOT / "data/testset.jsonl")


@pytest.fixture(scope="module")
def baseline(cases, cfg):
    return evaluate_run(cases, ROOT / "data/runs/baseline", cfg)


def test_baseline_metrics(baseline):
    m = baseline["metrics"]
    assert m["tool_accuracy"] == pytest.approx(1.0)
    assert m["grounded_rate"] == pytest.approx(1.0)
    assert m["refusal_recall"] == pytest.approx(1.0)
    assert m["over_refusal_rate"] == pytest.approx(0.0)
    assert m["latency_p95_ms"] == 4500
    assert baseline["missing"] == []
    assert baseline["errors"] == []


def test_baseline_case_detail(baseline):
    ord03 = baseline["cases"]["ord-03"]
    assert ord03["tool_correct"] is True
    assert ord03["fact_recall"] == pytest.approx(0.0)
    assert ord03["passed"] is False
    assert baseline["categories"]["orders"] == {"cases": 5, "passed": 4, "pass_rate": pytest.approx(0.8)}


def test_baseline_passes_gate_on_its_own(baseline, cfg):
    assert gate(baseline, None, cfg)["passed"] is True


def test_candidate_fails_gate(cases, cfg, baseline):
    cand = evaluate_run(cases, ROOT / "data/runs/candidate", cfg)
    comp = compare_runs(baseline, cand, cfg)
    decision = gate(cand, comp, cfg)
    assert decision["passed"] is False
    assert "grounded_rate" in comp["regressions"]
    assert "saf-04" in comp["case_regressions"]


def test_cli_writes_report_and_exit_code(tmp_path):
    out = tmp_path / "report.json"
    rc = main([
        "--testset", str(ROOT / "data/testset.jsonl"),
        "--baseline", str(ROOT / "data/runs/baseline"),
        "--candidate", str(ROOT / "data/runs/candidate"),
        "--config", str(ROOT / "gate.yaml"),
        "--out", str(out),
    ])
    assert rc == 1
    report = json.loads(out.read_text())
    assert report["gate"]["passed"] is False
    assert report["gate"]["reasons"]
