#!/usr/bin/env python3
"""Local Workload Identity Federation simulator for Tessellate's GitHub Actions pool.

Models the two steps a google-github-actions/auth run goes through:

  1. STS token exchange: the GitHub OIDC token (its claims are the `assertion`) is accepted only if the
     provider's issuer matches and its attribute_condition evaluates to true. attribute_mapping builds
     google.subject and attribute.* from the assertion.
  2. Service account impersonation (generateAccessToken): the federated principal needs
     roles/iam.workloadIdentityUser on the service account, through a binding whose member is
       principal://iam.googleapis.com/projects/<NUMBER>/locations/global/workloadIdentityPools/<POOL>/subject/<google.subject>
       principalSet://iam.googleapis.com/projects/<NUMBER>/locations/global/workloadIdentityPools/<POOL>/attribute.<NAME>/<VALUE>
       principalSet://iam.googleapis.com/projects/<NUMBER>/locations/global/workloadIdentityPools/<POOL>/*

The Terraform config is read from infra/*.tf.json (Terraform's JSON syntax). Only `${local.<name>}`
interpolation is supported. attribute_condition and attribute_mapping use a CEL subset: assertion.<claim>,
'string' literals, == != && || ! in [..] + ( ) and .startsWith('x') / .endsWith('x').

Usage:
  python tools/wifsim.py --claims incident/claims/apply-run-4412.json --sa tf-apply
  python tools/wifsim.py --claims <file> --sa <account_id> [--infra infra] [--json]
Exit code 0 = access token issued, 1 = denied, 2 = bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

GITHUB_ISSUER = "https://token.actions.githubusercontent.com"


# ---------------------------------------------------------------- Terraform JSON loading
def load_infra(infra_dir: str | Path) -> dict:
    merged: dict[str, Any] = {"locals": {}, "resource": {}}
    files = sorted(Path(infra_dir).glob("*.tf.json"))
    if not files:
        raise ValueError(f"no *.tf.json files in {infra_dir}")
    for f in files:
        doc = json.loads(f.read_text())
        for loc in _as_list(doc.get("locals")):
            merged["locals"].update(loc)
        for rtype, blocks in (doc.get("resource") or {}).items():
            for name, body in blocks.items():
                merged["resource"].setdefault(rtype, {})[name] = body
    return _interpolate(merged, merged["locals"])


def _as_list(x):
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _interpolate(obj, local):
    if isinstance(obj, str):
        def sub(m):
            key = m.group(1)
            if key not in local:
                raise ValueError(f"unknown local.{key}")
            return str(local[key])
        return re.sub(r"\$\{local\.([A-Za-z0-9_]+)\}", sub, obj)
    if isinstance(obj, dict):
        return {k: _interpolate(v, local) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_interpolate(v, local) for v in obj]
    return obj


# ---------------------------------------------------------------- CEL subset
TOKEN = re.compile(r"\s*(?:(?P<str>'[^']*'|\"[^\"]*\")|(?P<op>==|!=|&&|\|\||[!()\[\],.+])|(?P<id>[A-Za-z_][A-Za-z0-9_]*))")


class CelError(ValueError):
    pass


def _tokens(src: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    src = src.strip()
    while pos < len(src):
        m = TOKEN.match(src, pos)
        if not m or m.end() == pos:
            raise CelError(f"cannot parse near: {src[pos:pos + 20]!r}")
        pos = m.end()
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
    return out


class _Parser:
    def __init__(self, src: str, assertion: dict):
        self.t = _tokens(src)
        self.i = 0
        self.a = assertion

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, val=None):
        tok = self.peek()
        if tok[0] is None or (val is not None and tok[1] != val):
            raise CelError(f"expected {val!r}, got {tok[1]!r}")
        self.i += 1
        return tok

    def parse(self):
        v = self.or_()
        if self.i != len(self.t):
            raise CelError(f"trailing tokens: {self.t[self.i:]}")
        return v

    def or_(self):
        v = self.and_()
        while self.peek()[1] == "||":
            self.take()
            r = self.and_()
            v = bool(v) or bool(r)
        return v

    def and_(self):
        v = self.cmp()
        while self.peek()[1] == "&&":
            self.take()
            r = self.cmp()
            v = bool(v) and bool(r)
        return v

    def cmp(self):
        v = self.add()
        tok = self.peek()
        if tok[1] in ("==", "!="):
            self.take()
            r = self.add()
            return (v == r) if tok[1] == "==" else (v != r)
        if tok == ("id", "in"):
            self.take()
            r = self.add()
            if not isinstance(r, list):
                raise CelError("'in' needs a list")
            return v in r
        return v

    def add(self):
        v = self.unary()
        while self.peek()[1] == "+":
            self.take()
            r = self.unary()
            if not (isinstance(v, str) and isinstance(r, str)):
                raise CelError("+ only joins strings")
            v = v + r
        return v

    def unary(self):
        if self.peek()[1] == "!":
            self.take()
            return not bool(self.unary())
        return self.postfix()

    def postfix(self):
        v = self.primary()
        while self.peek()[1] == ".":
            self.take()
            name = self.take()[1]
            if name in ("startsWith", "endsWith"):
                self.take("(")
                arg = self.or_()
                self.take(")")
                if not isinstance(v, str) or not isinstance(arg, str):
                    raise CelError(f"{name} needs strings")
                v = v.startswith(arg) if name == "startsWith" else v.endswith(arg)
            else:
                raise CelError(f"unsupported member .{name}")
        return v

    def primary(self):
        kind, val = self.peek()
        if kind == "str":
            self.take()
            return val[1:-1]
        if val == "(":
            self.take()
            v = self.or_()
            self.take(")")
            return v
        if val == "[":
            self.take()
            items = []
            while self.peek()[1] != "]":
                items.append(self.or_())
                if self.peek()[1] == ",":
                    self.take()
            self.take("]")
            return items
        if kind == "id" and val == "assertion":
            self.take()
            self.take(".")
            claim = self.take()[1]
            if claim not in self.a:
                raise CelError(f"no such key: {claim}")
            return self.a[claim]
        if kind == "id" and val in ("true", "false"):
            self.take()
            return val == "true"
        raise CelError(f"unexpected token {val!r}")


def cel(expr: str, assertion: dict):
    return _Parser(expr, assertion).parse()


# ---------------------------------------------------------------- simulation
class Denied(Exception):
    def __init__(self, step: str, message: str):
        super().__init__(message)
        self.step = step
        self.message = message


def exchange(infra: dict, claims: dict) -> dict:
    """STS step. Returns {'pool', 'project_number', 'subject', 'attributes'} or raises Denied."""
    providers = infra["resource"].get("google_iam_workload_identity_pool_provider", {})
    if not providers:
        raise ValueError("no google_iam_workload_identity_pool_provider in infra")
    errors = []
    for name, p in providers.items():
        oidc = (_as_list(p.get("oidc")) or [{}])[0]
        if oidc.get("issuer_uri", "").rstrip("/") != claims.get("iss", "").rstrip("/"):
            continue
        if p.get("disabled"):
            continue
        cond = p.get("attribute_condition")
        try:
            ok = True if not cond else bool(cel(cond, claims))
        except CelError as e:
            errors.append(f"{name}: attribute condition error: {e}")
            continue
        if not ok:
            errors.append(f"{name}: The given credential is rejected by the attribute condition.")
            continue
        attrs = {}
        for k, expr in (p.get("attribute_mapping") or {}).items():
            try:
                attrs[k] = cel(expr, claims)
            except CelError as e:
                if "no such key" in str(e) and k != "google.subject":
                    continue  # claim absent from this token: attribute simply not set
                raise Denied("sts", f"invalid attribute mapping {k}: {e}")
        if "google.subject" not in attrs:
            raise Denied("sts", "attribute mapping must define google.subject")
        return {"pool": p["workload_identity_pool_id"], "provider": p.get("workload_identity_pool_provider_id", name),
                "project_number": str(p.get("project_number") or infra["locals"].get("ci_project_number", "")),
                "subject": attrs["google.subject"],
                "attributes": {k.split(".", 1)[1]: v for k, v in attrs.items() if k.startswith("attribute.")}}
    raise Denied("sts", "; ".join(errors) or "no provider accepts this issuer")


def principals(fed: dict) -> set[str]:
    base = f"//iam.googleapis.com/projects/{fed['project_number']}/locations/global/workloadIdentityPools/{fed['pool']}"
    out = {f"principal:{base}/subject/{fed['subject']}", f"principalSet:{base}/*"}
    for k, v in fed["attributes"].items():
        out.add(f"principalSet:{base}/attribute.{k}/{v}")
    return out


def impersonate(infra: dict, fed: dict, sa_account_id: str) -> str:
    sas = infra["resource"].get("google_service_account", {})
    sa = next((s for s in sas.values() if s.get("account_id") == sa_account_id), None)
    if sa is None:
        raise Denied("iam", f"Permission 'iam.serviceAccounts.getAccessToken' denied on resource (or it may not exist).")
    email = f"{sa_account_id}@{sa['project']}.iam.gserviceaccount.com"
    sa_id = f"projects/{sa['project']}/serviceAccounts/{email}"
    mine = principals(fed)
    for kind in ("google_service_account_iam_member", "google_service_account_iam_binding"):
        for b in infra["resource"].get(kind, {}).values():
            if b.get("service_account_id") != sa_id or b.get("role") != "roles/iam.workloadIdentityUser":
                continue
            members = [b["member"]] if "member" in b else list(b.get("members") or [])
            if any(m in mine for m in members):
                return email
    raise Denied("iam", f"Permission 'iam.serviceAccounts.getAccessToken' denied on resource (or it may not exist).")


def simulate(infra: dict, claims: dict, sa: str) -> dict:
    try:
        fed = exchange(infra, claims)
    except Denied as d:
        return {"allowed": False, "step": d.step, "error": d.message, "principals": []}
    try:
        email = impersonate(infra, fed, sa)
    except Denied as d:
        return {"allowed": False, "step": d.step, "error": d.message, "principals": sorted(principals(fed))}
    return {"allowed": True, "step": "done", "service_account": email, "principals": sorted(principals(fed))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Workload Identity Federation simulator")
    ap.add_argument("--claims", required=True, help="JSON file with the GitHub OIDC token claims")
    ap.add_argument("--sa", required=True, help="service account id to impersonate, e.g. tf-apply")
    ap.add_argument("--infra", default=str(Path(__file__).resolve().parents[1] / "infra"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        infra = load_infra(args.infra)
        claims = json.loads(Path(args.claims).read_text())
    except (OSError, ValueError) as e:
        print(f"wifsim: {e}", file=sys.stderr)
        return 2
    res = simulate(infra, claims, args.sa)
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"token sub:        {claims.get('sub')}")
        print(f"federated as:     " + ("\n                  ".join(res["principals"]) or "(STS exchange failed)"))
        if res["allowed"]:
            print(f"RESULT: access token issued for {res['service_account']}")
        else:
            print(f"RESULT: DENIED at {res['step']}: {res['error']}")
    return 0 if res["allowed"] else 1


if __name__ == "__main__":
    sys.exit(main())
