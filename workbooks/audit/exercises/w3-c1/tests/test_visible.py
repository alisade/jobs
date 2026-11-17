"""Visible tests. make test"""

from conftest import SAMPLE, run
from scripts import happy

from tester.agent import run_test
from tester.scripted import ScriptedLlm


def test_happy_path_records_three_results():
    script, _ = happy()
    out = run(run_test(ScriptedLlm(script=script), SAMPLE))
    assert out.status == "ok", out.problems
    assert out.results["CHG-104390"]["result"] == "exception"
    assert len(out.log) == 13
