from __future__ import annotations

import re

SUPPORTED_KEYS = ("sub", "aud", "amr")


def _wild(p: str, v: str) -> bool:
    return re.match("^" + re.escape(p).replace(r"\*", ".*").replace(r"\?", ".") + "$", v) is not None


def _list(v):
    return v if isinstance(v, list) else [v]


def check(policy: dict, claims: dict, account: str) -> tuple[bool, str]:
    """Return (allowed, reason) for AssumeRoleWithWebIdentity with these claims."""
    host = claims["iss"].replace("https://", "").rstrip("/")
    provider_arn = f"arn:aws:iam::{account}:oidc-provider/{host}"
    for i, st in enumerate(_list(policy["Statement"])):
        if st.get("Effect") != "Allow":
            continue
        if "sts:AssumeRoleWithWebIdentity" not in _list(st.get("Action", [])):
            continue
        fed = _list(st.get("Principal", {}).get("Federated", []))
        if provider_arn not in fed:
            continue
        ok = True
        for op, block in (st.get("Condition") or {}).items():
            for key, expected in block.items():
                prov, _, claim = key.partition(":")
                if prov != host or claim not in SUPPORTED_KEYS:
                    return False, f"statement {i}: condition key {key} is not available for this provider"
                actual = claims.get(claim)
                if actual is None:
                    ok = op.startswith("StringNot")
                    continue
                exp = [str(x) for x in _list(expected)]
                if op == "StringEquals":
                    hit = str(actual) in exp
                elif op == "StringLike":
                    hit = any(_wild(e, str(actual)) for e in exp)
                elif op == "StringNotEquals":
                    hit = str(actual) not in exp
                elif op == "StringNotLike":
                    hit = not any(_wild(e, str(actual)) for e in exp)
                else:
                    return False, f"statement {i}: unsupported operator {op}"
                if not hit:
                    ok = False
        if ok:
            return True, f"allowed by statement {i}"
    return False, "AccessDenied: Not authorized to perform sts:AssumeRoleWithWebIdentity"
