"""Hidden tests for ms/w10-t1: description quality checks plus the full routing regression set."""
import itertools
import pathlib
import re

import pytest
import yaml

from proxy_router_hidden import router_for, tokens

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AGENT = ROOT / "agent"
TOOLS = {p.name[:-10]: yaml.safe_load(p.read_text()) for p in sorted((AGENT / "tools").glob("*.tool.yaml"))}
NEG = re.compile(r"\b(not|never|don't|doesn't|only for|instead)\b", re.I)

ROUTING = [
    ("how many vacation days do I have left?", "tool:GetPtoBalance"),
    ("what's my PTO balance", "tool:GetPtoBalance"),
    ("how much annual leave have I got remaining", "tool:GetPtoBalance"),
    ("check my remaining sick days", "tool:GetPtoBalance"),
    ("I want to book vacation from June 3 to June 7", "tool:SubmitLeaveRequest"),
    ("submit a leave request for next Friday", "tool:SubmitLeaveRequest"),
    ("request time off for my wedding", "tool:SubmitLeaveRequest"),
    ("apply for sick leave starting tomorrow", "tool:SubmitLeaveRequest"),
    ("when is the next public holiday", "topic:HolidayCalendar"),
    ("is the office closed on Thanksgiving", "topic:HolidayCalendar"),
    ("what is the policy on carrying over unused vacation", "knowledge:HRPolicyHandbook"),
    ("how does parental leave work", "knowledge:HRPolicyHandbook"),
]


def desc(name):
    return str(TOOLS[name].get("modelDescription") or "")


def test_both_tools_still_exist_with_original_operations():
    assert TOOLS["GetPtoBalance"]["action"]["operationId"] == "GetTimeOffBalances"
    assert TOOLS["SubmitLeaveRequest"]["action"]["operationId"] == "SubmitTimeOffRequest"
    assert not TOOLS["GetPtoBalance"].get("disabled") and not TOOLS["SubmitLeaveRequest"].get("disabled")


def test_other_components_untouched_in_existence():
    assert (AGENT / "topics" / "HolidayCalendar.topic.yaml").exists()
    assert (AGENT / "knowledge" / "HRPolicyHandbook.knowledge.yaml").exists()


def test_tool_display_names_are_distinct_and_specific():
    a = str(TOOLS["GetPtoBalance"].get("modelDisplayName") or "").lower()
    b = str(TOOLS["SubmitLeaveRequest"].get("modelDisplayName") or "").lower()
    assert a and b and a != b
    assert set(tokens(a)) != set(tokens(b))


def test_tool_descriptions_are_not_copies():
    a, b = set(tokens(desc("GetPtoBalance"))), set(tokens(desc("SubmitLeaveRequest")))
    jac = len(a & b) / max(1, len(a | b))
    assert jac < 0.5, f"descriptions overlap too much (Jaccard {jac:.2f})"


@pytest.mark.parametrize("name", ["GetPtoBalance", "SubmitLeaveRequest"])
def test_description_length_and_no_keyword_stuffing(name):
    d = desc(name)
    assert 60 <= len(d) <= 500, f"{name}: description length {len(d)} outside 60-500"
    counts = {t: c for t, c in ((t, tokens(d).count(t)) for t in set(tokens(d)))}
    worst = max(counts.values()) if counts else 0
    assert worst <= 3, f"{name}: a word is repeated {worst} times; describe, don't stuff"
    whole = d + " ".join(str(i.get("description") or "") for i in TOOLS[name].get("inputs") or [])
    assert len(whole) <= 900


@pytest.mark.parametrize("name", ["GetPtoBalance", "SubmitLeaveRequest"])
def test_description_says_what_it_does_not_do(name):
    assert NEG.search(desc(name)), f"{name}: add a sentence saying what this tool does NOT do"


def test_all_tool_inputs_described():
    for name, d in TOOLS.items():
        for i in d.get("inputs") or []:
            if i.get("kind") == "AutomaticTaskInput":
                assert len(str(i.get("description") or "")) >= 20, f"{name}.{i['propertyName']} needs a description"


@pytest.mark.parametrize("utterance,expected", ROUTING)
def test_routing_regression_set(utterance, expected):
    r = router_for(AGENT)
    assert r.route(utterance) == expected, r.scores(utterance)[:3]


def test_answer_names_the_overlap():
    text = (ROOT / "ANSWER.md").read_text().lower()
    assert "description" in text and re.search(r"cop(y|ied)|duplicat|identical|same", text)
