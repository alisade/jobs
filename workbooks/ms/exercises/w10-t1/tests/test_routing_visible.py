"""Visible tests: a slice of the regression test set, through the proxy router."""
import pathlib

import pytest
import yaml

from proxy_router import router_for

AGENT = pathlib.Path(__file__).resolve().parent.parent / "agent"

CASES = [
    ("how many vacation days do I have left?", "tool:GetPtoBalance"),
    ("what's my PTO balance", "tool:GetPtoBalance"),
    ("I want to book vacation from June 3 to June 7", "tool:SubmitLeaveRequest"),
    ("submit a leave request for next Friday", "tool:SubmitLeaveRequest"),
    ("when is the next public holiday", "topic:HolidayCalendar"),
    ("what is the policy on carrying over unused vacation", "knowledge:HRPolicyHandbook"),
]


@pytest.mark.parametrize("utterance,expected", CASES)
def test_routes_to_expected_component(utterance, expected):
    r = router_for(AGENT)
    assert r.route(utterance) == expected, r.scores(utterance)[:3]


def test_every_tool_input_has_a_description():
    for p in (AGENT / "tools").glob("*.tool.yaml"):
        d = yaml.safe_load(p.read_text())
        for i in d.get("inputs") or []:
            if i.get("kind") == "AutomaticTaskInput":
                assert len(str(i.get("description") or "")) >= 20, f"{p.name}: input {i['propertyName']} needs a description"
