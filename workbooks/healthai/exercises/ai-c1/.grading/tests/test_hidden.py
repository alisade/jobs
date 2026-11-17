"""Hidden tests for healthai/ai-c1."""

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

from evals.gates import evaluate, main, p95, wilson_lower

FIX = Path(__file__).resolve().parent.parent / "fixtures"
GATES = {"regress_schema": "schema_validity", "regress_citation": "citation_support",
         "regress_accuracy": "criteria_accuracy", "regress_safety": "safety", "regress_variance": "consistency"}


def run(name):
    return evaluate(FIX / "runs" / name, json.loads((FIX / "cases.json").read_text()),
                    json.loads((FIX / "policy.json").read_text()), json.loads((FIX / "baseline.json").read_text()))


@pytest.mark.parametrize("variant,gate", sorted(GATES.items()))
def test_each_regression_trips_exactly_its_gate(variant, gate):
    r = run(variant)
    failed = sorted(k for k, g in r["gates"].items() if not g["passed"])
    assert failed == [gate]
    assert not r["passed"]


def test_good_values():
    r = run("good")
    g = r["gates"]
    assert g["schema_validity"]["value"] == 1.0 and g["safety"]["value"] == 0
    assert g["citation_support"]["value"] == 1.0
    assert abs(g["criteria_accuracy"]["value"] - 177 / 180) < 1e-9
    assert g["consistency"]["value"] == 1.0
    assert r["runs"] == 3


def test_statistical_gates_use_wilson_lower_bound():
    r = run("good")
    g = r["gates"]["criteria_accuracy"]
    assert abs(g["lower"] - wilson_lower(177, 180)) < 1e-9


@pytest.mark.parametrize("k,n,expected", [(9, 10, 0.5958), (50, 50, 0.9287), (0, 10, 0.0), (180, 200, 0.8506)])
def test_wilson_values(k, n, expected):
    assert abs(wilson_lower(k, n) - expected) < 1e-3


def test_wilson_empty_is_zero():
    assert wilson_lower(0, 0) == 0.0


def test_p95_nearest_rank():
    assert p95(list(range(1, 101))) == 95
    assert p95([5]) == 5
    assert p95([3, 1, 2, 10]) == 10


def test_cost_and_latency():
    r = run("good")
    rows = [row for p in sorted((FIX / "runs" / "good").glob("run*.json")) for row in json.loads(p.read_text())]
    exp = sum(x["input_tokens"] * 1.25 + x["output_tokens"] * 10.0 for x in rows) / 1e6 / 3
    assert math.isclose(r["cost_usd_per_run"], exp, rel_tol=1e-3)
    assert r["p95_latency_ms"] == p95([x["latency_ms"] for x in rows])


def test_safety_lists_the_violation():
    v = run("regress_safety")["gates"]["safety"]
    assert v["value"] == 1 and v["violations"] == ["run3:EV-008"]


def test_cli_exit_codes_and_summary(tmp_path):
    good = tmp_path / "good.md"
    assert main(["x", str(FIX / "runs" / "good"), str(FIX), str(good)]) == 0
    text = good.read_text()
    for name in GATES.values():
        assert name in text
    assert "PASS" in text and "$" in text
    bad = tmp_path / "bad.md"
    assert main(["x", str(FIX / "runs" / "regress_citation"), str(FIX), str(bad)]) == 1
    assert "FAIL" in bad.read_text()


def test_cli_as_module(tmp_path):
    p = subprocess.run([sys.executable, "-m", "evals.gates", str(FIX / "runs" / "regress_schema"), str(FIX)],
                       cwd=FIX.parent, capture_output=True, text=True, timeout=60)
    assert p.returncode == 1
