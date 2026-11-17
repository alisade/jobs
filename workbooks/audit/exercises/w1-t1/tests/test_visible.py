"""Visible test: the Q3 run must not be all-pass when the reviewer found exceptions. make test"""

from controlpilot import data, pipeline
from controlpilot.fake_gemini import FakeClient


def test_reviewer_spot_check_exceptions_are_found():
    results = {r.sample_id: r for r in pipeline.run(FakeClient(), data.samples(), data.deploys(), data.directory())}
    assert results["S07"].result == "exception"
    assert results["S18"].result == "exception"
    assert results["S03"].result == "pass"
