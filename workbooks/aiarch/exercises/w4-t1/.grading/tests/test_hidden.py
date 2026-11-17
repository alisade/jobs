import json
from pathlib import Path

import pytest

from authz.engine import authorize, load_policies, validate

HERE = Path(__file__).resolve().parent
CASES = [json.loads(l) for l in (HERE / "requests_hidden.jsonl").read_text().splitlines() if l.strip()]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_hidden_decision(case):
    r = authorize(case["claims"], case["tool"], case["input"])
    assert r.decision == case["expect"], f"{case['name']}: got {r.decision} reasons={r.reasons} errors={r.errors}"


def test_policy_set_validates_against_schema():
    errs = validate()
    assert not errs, errs


def test_no_evaluation_errors_on_contractor_requests():
    c = {"preferred_username": "vk-ext-0042", "role": "manager", "idp": "partner"}
    r = authorize(c, "approve_access_request", {"request_id": "AR-9", "team": "payments", "requester": "jdiaz"})
    assert r.decision == "DENY" and not r.errors, r.errors


def test_still_five_policies_and_forbids_kept():
    text = load_policies()
    assert text.count("forbid(") >= 2 and text.count("permit(") == 3, "fix the policy, do not delete the guard rails"


def test_answer_explains_error_skip():
    t = Path("ANSWER.md").read_text().lower()
    assert "has" in t and ("error" in t or "skipped" in t)
