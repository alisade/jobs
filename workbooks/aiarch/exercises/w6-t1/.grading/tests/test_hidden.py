import json
from pathlib import Path

import pytest

from scpsim import evaluate, load_org, load_policy

EX = Path.cwd()
HERE = Path(__file__).resolve().parent
REQS = json.loads((HERE / "requests_hidden.json").read_text())


@pytest.fixture(scope="module")
def org():
    return load_org(EX / "org/layout.json", EX / "policies/attachments.json", EX / "policies")


@pytest.mark.parametrize("req", REQS, ids=[r["name"] for r in REQS])
def test_hidden_request(org, req):
    d = evaluate(org, req)
    got = "ALLOW" if d.allowed else "DENY"
    assert got == req["expect"], f"{req['name']}: expected {req['expect']}, got {got} ({d.reason} {d.denied_by})"


def test_change_control_still_attached_to_workloads():
    att = json.loads((EX / "policies/attachments.json").read_text())
    assert "scp-iam-change-control" in att["scps"]["Workloads"]


def test_no_blanket_cdk_exemption():
    doc = load_policy(EX / "policies/scp-iam-change-control.json")
    text = json.dumps(doc)
    assert "role/cdk-*" not in text and "role/*" not in text


def test_other_guardrails_untouched():
    sol = {"scp-region-guardrail", "scp-protect-audit", "scp-org-membership", "scp-bedrock-models", "scp-prod-private-bedrock", "rcp-org-boundary"}
    for n in sol:
        assert (EX / "policies" / f"{n}.json").exists()


def test_answer_names_cfn_exec_role():
    t = (EX / "ANSWER.md").read_text().lower()
    assert "cfn-exec" in t and ("cloudformation" in t)
