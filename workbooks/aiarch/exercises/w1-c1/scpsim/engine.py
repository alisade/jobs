"""Evaluation engine for scpsim (see package docstring)."""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

NEGATED = {"StringNotEquals", "StringNotLike", "ArnNotEquals", "ArnNotLike", "NumericNotEquals",
           "StringNotEqualsIgnoreCase"}


@dataclass
class Decision:
    allowed: bool
    reason: str
    denied_by: list[str] = field(default_factory=list)  # "<policy>:<sid>"

    def __bool__(self) -> bool:  # pragma: no cover - convenience only
        return self.allowed


@dataclass
class Org:
    """Org layout plus attachments. ``ous`` maps OU name -> parent ("Root" for top level);
    ``accounts`` maps account id -> {"name", "ou"}; ``scps`` / ``rcps`` map a target
    ("Root", an OU name or an account id) -> list of policy names; ``policies`` maps policy
    name -> parsed document."""

    management_account: str
    ous: dict[str, str]
    accounts: dict[str, dict[str, str]]
    scps: dict[str, list[str]]
    rcps: dict[str, list[str]]
    policies: dict[str, dict]

    def path(self, account: str) -> list[str]:
        if account not in self.accounts:
            raise KeyError(f"unknown account {account}")
        chain = [account]
        ou = self.accounts[account]["ou"]
        while ou != "Root":
            chain.append(ou)
            if ou not in self.ous:
                raise KeyError(f"unknown OU {ou}")
            ou = self.ous[ou]
        chain.append("Root")
        return list(reversed(chain))


def load_policy(path: str | Path) -> dict:
    doc = json.loads(Path(path).read_text())
    if doc.get("Version") != "2012-10-17":
        raise ValueError(f"{path}: Version must be 2012-10-17")
    st = doc.get("Statement")
    if isinstance(st, dict):
        doc["Statement"] = [st]
    return doc


def policy_size(doc: dict) -> int:
    """Characters AWS counts against the 5,120 limit (whitespace removed, as the API stores it)."""
    return len(json.dumps(doc, separators=(",", ":")))


def load_org(layout_path: str | Path, attachments_path: str | Path, policy_dir: str | Path) -> Org:
    layout = json.loads(Path(layout_path).read_text())
    att = json.loads(Path(attachments_path).read_text())
    pdir = Path(policy_dir)
    names = set()
    for kind in ("scps", "rcps"):
        for targets in att.get(kind, {}).values():
            names.update(targets)
    policies: dict[str, dict] = {}
    for n in sorted(names):
        if n in ("FullAWSAccess", "RCPFullAWSAccess"):
            continue
        p = pdir / f"{n}.json"
        if not p.exists():
            raise FileNotFoundError(f"attachments.json names {n} but {p} does not exist")
        policies[n] = load_policy(p)
    policies["FullAWSAccess"] = {"Version": "2012-10-17", "Statement": [
        {"Sid": "FullAWSAccess", "Effect": "Allow", "Action": "*", "Resource": "*"}]}
    return Org(
        management_account=layout["management_account"],
        ous=layout["ous"],
        accounts=layout["accounts"],
        scps=att.get("scps", {}),
        rcps=att.get("rcps", {}),
        policies=policies,
    )


# ---------------------------------------------------------------- matching helpers

def _as_list(v: Any) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def _wild(pattern: str, value: str, ignore_case: bool) -> bool:
    if ignore_case:
        pattern, value = pattern.lower(), value.lower()
    rx = "^" + re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".") + "$"
    return re.match(rx, value, flags=re.S) is not None


def _action_match(patterns: list[str], action: str) -> bool:
    return any(_wild(p, action, True) for p in patterns)


def _resource_match(patterns: list[str], resource: str) -> bool:
    return any(_wild(p, resource, False) for p in patterns)


def _arn_like(pattern: str, value: str) -> bool:
    # ArnLike compares the six ARN parts separately; wildcards do not cross ':' except in the
    # resource part, which keeps its own wildcard semantics.
    pp, vp = pattern.split(":", 5), value.split(":", 5)
    if len(pp) != 6 or len(vp) != 6:
        return False
    return all(_wild(a, b, False) for a, b in zip(pp, vp))


def _num(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _match_one(op: str, expected: str, actual: Any) -> bool:
    base = op
    if base in ("StringEquals", "StringNotEquals"):
        return str(actual) == str(expected)
    if base in ("StringEqualsIgnoreCase", "StringNotEqualsIgnoreCase"):
        return str(actual).lower() == str(expected).lower()
    if base in ("StringLike", "StringNotLike"):
        return _wild(str(expected), str(actual), False)
    if base in ("ArnEquals", "ArnNotEquals"):
        return str(actual) == str(expected)
    if base in ("ArnLike", "ArnNotLike"):
        return _arn_like(str(expected), str(actual))
    if base == "Bool":
        return str(actual).lower() == str(expected).lower()
    if base.startswith("Numeric"):
        a, e = _num(actual), _num(expected)
        if a is None or e is None:
            return False
        return {
            "NumericEquals": a == e, "NumericNotEquals": a == e, "NumericLessThan": a < e,
            "NumericLessThanEquals": a <= e, "NumericGreaterThan": a > e,
            "NumericGreaterThanEquals": a >= e,
        }[base]
    raise ValueError(f"unsupported condition operator {op}")


def _condition_holds(raw_op: str, key: str, expected_values: list, ctx: dict) -> bool:
    op = raw_op
    set_mode = None
    if op.startswith("ForAnyValue:"):
        set_mode, op = "any", op[len("ForAnyValue:"):]
    elif op.startswith("ForAllValues:"):
        set_mode, op = "all", op[len("ForAllValues:"):]
    if_exists = op.endswith("IfExists")
    if if_exists:
        op = op[: -len("IfExists")]
    present = key in ctx and ctx[key] is not None

    if op == "Null":
        want_null = str(expected_values[0]).lower() == "true"
        return (not present) == want_null

    if not present:
        if if_exists:
            return True
        if set_mode == "all":
            return True
        if set_mode == "any":
            return False
        return op in NEGATED

    negated = op in NEGATED
    actual_values = _as_list(ctx[key])

    def matches(actual: Any) -> bool:
        hit = any(_match_one(op, e, actual) for e in expected_values)
        return (not hit) if negated else hit

    if set_mode == "any":
        return any(matches(a) for a in actual_values)
    if set_mode == "all":
        return all(matches(a) for a in actual_values)
    if len(actual_values) != 1:
        # single-valued operator against a multi-valued key: treat like ForAnyValue (IAM's
        # behavior is undefined here; policies should use a set prefix instead)
        return any(matches(a) for a in actual_values)
    return matches(actual_values[0])


def _conditions_hold(cond: dict | None, ctx: dict) -> bool:
    if not cond:
        return True
    for op, block in cond.items():
        for key, expected in block.items():
            if not _condition_holds(op, key, [str(x) for x in _as_list(expected)], ctx):
                return False
    return True


def _statement_applies(st: dict, action: str, resource: str, ctx: dict) -> bool:
    if "Action" in st and not _action_match(_as_list(st["Action"]), action):
        return False
    if "NotAction" in st and _action_match(_as_list(st["NotAction"]), action):
        return False
    if "Resource" in st and not _resource_match(_as_list(st["Resource"]), resource):
        return False
    if "NotResource" in st and _resource_match(_as_list(st["NotResource"]), resource):
        return False
    return _conditions_hold(st.get("Condition"), ctx)


def _context(request: dict) -> dict:
    ctx = dict(request.get("context", {}))
    ctx.setdefault("aws:PrincipalArn", request["principal_arn"])
    ctx.setdefault("aws:RequestedRegion", request.get("region"))
    ctx.setdefault("aws:PrincipalAccount", request.get("principal_account") or request["account"])
    return ctx


def _is_service_linked(principal_arn: str) -> bool:
    return ":role/aws-service-role/" in principal_arn


def evaluate(org: Org, request: dict) -> Decision:
    """Evaluate one request.

    request keys: account (the principal's account), principal_arn, action, resource,
    region, optional resource_account (defaults to account), optional context (condition keys).
    """
    action, resource = request["action"], request.get("resource", "*")
    ctx = _context(request)
    principal_acct = request["account"]
    resource_acct = request.get("resource_account", principal_acct)
    denied: list[str] = []

    # ---- SCPs (principal side)
    if principal_acct != org.management_account and not _is_service_linked(request["principal_arn"]):
        if principal_acct not in org.accounts:
            # principal outside the org: SCPs of this org do not apply to it
            pass
        else:
            for target in org.path(principal_acct):
                attached = org.scps.get(target, [])
                if not attached:
                    return Decision(False, f"no SCP attached at {target} (implicit deny)")
                level_allows = False
                for name in attached:
                    for st in org.policies[name]["Statement"]:
                        if not _statement_applies(st, action, resource, ctx):
                            continue
                        if st["Effect"] == "Deny":
                            denied.append(f"{name}:{st.get('Sid', '?')}")
                        elif st["Effect"] == "Allow":
                            level_allows = True
                if not level_allows and not denied:
                    return Decision(False, f"no SCP at {target} allows {action} (implicit deny)")
    # ---- RCPs (resource side)
    if (resource_acct in org.accounts and resource_acct != org.management_account
            and not _is_service_linked(request["principal_arn"])):
        for target in org.path(resource_acct):
            for name in org.rcps.get(target, []):
                if name == "RCPFullAWSAccess":
                    continue
                for st in org.policies[name]["Statement"]:
                    if st["Effect"] == "Deny" and _statement_applies(st, action, resource, ctx):
                        denied.append(f"{name}:{st.get('Sid', '?')}")
    if denied:
        return Decision(False, "explicit deny in an organization policy", denied)
    return Decision(True, "allowed by organization policies (identity and resource policies not modeled)")
