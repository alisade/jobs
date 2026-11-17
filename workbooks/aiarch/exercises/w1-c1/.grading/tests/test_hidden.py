"""Hidden tests for aiarch/w1-c1: more requests (cross-Region inference, exemptions, RCP edge
cases) and structural rules for production SCPs/RCPs."""

import json
from pathlib import Path

import pytest

from scpsim import evaluate, load_org, load_policy, policy_size

EX = Path.cwd()
HERE = Path(__file__).resolve().parent
REQS = json.loads((HERE / "requests_hidden.json").read_text())
LAYOUT = json.loads((EX / "org/layout.json").read_text())
ATT = json.loads((EX / "policies/attachments.json").read_text())


@pytest.fixture(scope="module")
def org():
    return load_org(EX / "org/layout.json", EX / "policies/attachments.json", EX / "policies")


@pytest.mark.parametrize("req", REQS, ids=[r["name"] for r in REQS])
def test_hidden_request(org, req):
    d = evaluate(org, req)
    got = "ALLOW" if d.allowed else "DENY"
    assert got == req["expect"], f"{req['name']}: expected {req['expect']}, got {got} ({d.reason} {d.denied_by})"


def _custom(kind):
    names = set()
    for targets in ATT.get(kind, {}).values():
        names.update(t for t in targets if t not in ("FullAWSAccess", "RCPFullAWSAccess"))
    return {n: load_policy(EX / "policies" / f"{n}.json") for n in sorted(names)}


def test_full_aws_access_kept_on_every_target():
    targets = ["Root", *LAYOUT["ous"].keys(), *LAYOUT["accounts"].keys()]
    missing = [t for t in targets if "FullAWSAccess" not in ATT["scps"].get(t, [])]
    assert not missing, f"FullAWSAccess must stay attached (deny-list strategy, no lockout): {missing}"


def test_all_six_policies_attached():
    names = set(_custom("scps")) | set(_custom("rcps"))
    want = {"scp-region-guardrail", "scp-protect-audit", "scp-org-membership", "scp-bedrock-models",
            "scp-prod-private-bedrock", "rcp-org-boundary"}
    assert want <= names, f"not attached: {sorted(want - names)}"


def test_custom_policies_are_deny_only_with_sids():
    for name, doc in {**_custom("scps"), **_custom("rcps")}.items():
        for st in doc["Statement"]:
            assert st.get("Effect") == "Deny", f"{name}: custom guardrails are deny statements (found {st.get('Effect')})"
            assert st.get("Sid") and st["Sid"].isalnum(), f"{name}: every statement needs an alphanumeric Sid"


def test_size_limits():
    for name, doc in {**_custom("scps"), **_custom("rcps")}.items():
        assert policy_size(doc) <= 5120, f"{name} is {policy_size(doc)} characters (limit 5120)"


def test_rcp_shape():
    rcps = _custom("rcps")
    assert rcps, "attach rcp-org-boundary at Root"
    allowed_services = {"s3", "sts", "kms", "sqs", "secretsmanager"}
    for name, doc in rcps.items():
        for st in doc["Statement"]:
            assert st.get("Principal") == "*", f"{name}: RCP statements must use Principal \"*\""
            actions = st.get("Action", [])
            actions = actions if isinstance(actions, list) else [actions]
            assert "*" not in actions, f"{name}: Action \"*\" is not allowed in an RCP"
            for a in actions:
                assert a.split(":")[0] in allowed_services, f"{name}: {a} is not an RCP-supported service here"


def test_bedrock_models_not_attached_to_root():
    assert "scp-bedrock-models" not in ATT["scps"].get("Root", []), \
        "attach the model allow-list to the OUs that run agents (Workloads, Sandbox), not to Root"
