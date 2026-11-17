import json
from pathlib import Path

from evals.gates import evaluate

FIX = Path(__file__).resolve().parent.parent / "fixtures"


def run(name):
    return evaluate(FIX / "runs" / name, json.loads((FIX / "cases.json").read_text()),
                    json.loads((FIX / "policy.json").read_text()), json.loads((FIX / "baseline.json").read_text()))


def test_good_runs_pass_every_gate():
    r = run("good")
    assert set(r["gates"]) == {"schema_validity", "citation_support", "criteria_accuracy", "safety", "consistency"}
    assert r["passed"]


def test_a_single_auto_denial_fails_the_build():
    r = run("regress_safety")
    assert not r["passed"] and not r["gates"]["safety"]["passed"]
