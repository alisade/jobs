"""Evaluate a gateway tool call against the Cedar policy set with cedarpy (works as shipped).

Like Policy in AgentCore, the principal comes from the verified token's claims, the action is
the tool name and context.input carries the tool arguments. Claims the IdP did not send are
simply absent from the principal (the partner IdP sends no "team" claim).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cedarpy

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Result:
    decision: str          # "ALLOW" or "DENY"
    reasons: list[str]     # determining policy ids
    errors: list[str]      # evaluation errors (a policy that errors is skipped)


def principal_from_claims(claims: dict) -> dict:
    attrs = {"role": claims["role"], "username": claims["preferred_username"], "idp": claims.get("idp", "workforce")}
    if "team" in claims:
        attrs["team"] = claims["team"]
    return {"uid": {"type": "User", "id": claims["preferred_username"]}, "attrs": attrs, "parents": []}


def load_policies(path: Path | None = None) -> str:
    return (path or ROOT / "policies" / "gateway.cedar").read_text()


def authorize(claims: dict, tool: str, args: dict, policies: str | None = None) -> Result:
    pol = policies if policies is not None else load_policies()
    principal = principal_from_claims(claims)
    entities = [principal, {"uid": {"type": "Gateway", "id": "lighthouse-tools"}, "attrs": {}, "parents": []}]
    req = {"principal": f'User::"{principal["uid"]["id"]}"', "action": f'Action::"{tool}"',
           "resource": 'Gateway::"lighthouse-tools"', "context": {"input": args}}
    r = cedarpy.is_authorized(req, pol, entities)
    return Result("ALLOW" if r.decision == cedarpy.Decision.Allow else "DENY",
                  list(r.diagnostics.reasons), list(r.diagnostics.errors))


def validate(policies: str | None = None) -> list[str]:
    schema = (ROOT / "policies" / "schema.json").read_text()
    v = cedarpy.validate_policies(policies if policies is not None else load_policies(), schema)
    return [f"{e.policy_id}: {e.error}" for e in (v.errors or [])]


if __name__ == "__main__":  # python -m authz.engine requests.jsonl
    import sys
    for line in Path(sys.argv[1]).read_text().splitlines():
        if not line.strip():
            continue
        c = json.loads(line)
        r = authorize(c["claims"], c["tool"], c["input"])
        flag = "" if "expect" not in c else ("ok      " if c["expect"] == r.decision else "MISMATCH")
        print(f"{flag:8} {r.decision:5} {c['name']}  reasons={r.reasons} errors={len(r.errors)}")
    errs = validate()
    print("schema validation:", "passed" if not errs else "; ".join(errs))
