#!/usr/bin/env python3
"""Foundation guardrails for Tessellate's GCP org, evaluated on a Terraform plan.

Input is the JSON from `terraform show -json tfplan` (format_version 1.x). Every rule looks at the
planned state of each resource change (`change.after`), the way `gcloud beta terraform vet` checks a
plan rather than the HCL. Resources being destroyed are not evaluated.

Usage:
  python guardrails.py plans/foundation.plan.json [--policy policy.yaml] [--json]
Exit codes: 0 no errors, 1 at least one error finding, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterator

import yaml

UNKNOWN = object()  # sentinel for values Terraform only knows after apply


@dataclass(frozen=True)
class Finding:
    rule: str
    address: str
    severity: str  # "error" or "warning"
    message: str


@dataclass
class Resource:
    address: str
    type: str
    after: dict
    after_unknown: dict

    def get(self, key: str, default: Any = None) -> Any:
        """Value of a top-level attribute, or UNKNOWN when it is computed at apply time."""
        if isinstance(self.after_unknown, dict) and self.after_unknown.get(key) is True:
            return UNKNOWN
        return self.after.get(key, default)


def load_plan(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict) or "resource_changes" not in data:
        raise ValueError(f"{path}: not a terraform show -json plan (no resource_changes)")
    return data


def load_policy(path: str | Path) -> dict:
    return yaml.safe_load(Path(path).read_text())


def resources(plan: dict) -> Iterator[Resource]:
    for rc in plan.get("resource_changes", []):
        if rc.get("mode", "managed") != "managed":
            continue
        change = rc.get("change") or {}
        actions = change.get("actions") or []
        after = change.get("after")
        if after is None or actions == ["delete"]:
            continue
        yield Resource(rc["address"], rc["type"], after, change.get("after_unknown") or {})


RULES: list[tuple[str, Callable[[Resource, dict, dict], Iterator[Finding]]]] = []


def rule(rule_id: str):
    def wrap(fn):
        RULES.append((rule_id, fn))
        return fn
    return wrap


def unknown(rule_id: str, r: Resource, attr: str) -> Finding:
    return Finding(rule_id, r.address, "warning", f"{attr} is unknown until apply; re-check after apply")


# ---- GR001 no service account keys --------------------------------------------------------
@rule("GR001")
def no_sa_keys(r: Resource, policy: dict, ctx: dict):
    if r.type == "google_service_account_key":
        yield Finding("GR001", r.address, "error",
                      "service account keys are not allowed; use Workload Identity Federation or impersonation")


# ---- GR002 / GR003 IAM ----------------------------------------------------------------------
IAM_TYPES = {
    "google_organization_iam_member": "organization", "google_organization_iam_binding": "organization",
    "google_folder_iam_member": "folder", "google_folder_iam_binding": "folder",
    "google_project_iam_member": "project", "google_project_iam_binding": "project",
}


def iam_members(r: Resource) -> list[str]:
    if r.type.endswith("_member"):
        m = r.get("member")
        return [] if m is UNKNOWN or m is None else [m]
    ms = r.get("members")
    return [] if ms is UNKNOWN or ms is None else list(ms)


@rule("GR002")
def no_basic_roles(r: Resource, policy: dict, ctx: dict):
    if r.type not in IAM_TYPES:
        return
    role = r.get("role")
    if role is UNKNOWN:
        yield unknown("GR002", r, "role")
    elif role in set(policy.get("basic_roles", [])):
        yield Finding("GR002", r.address, "error",
                      f"basic role {role} granted on a {IAM_TYPES[r.type]}; use predefined or custom roles")


@rule("GR003")
def no_users_high_in_tree(r: Resource, policy: dict, ctx: dict):
    if IAM_TYPES.get(r.type) not in ("organization", "folder"):
        return
    for m in iam_members(r):
        if m.startswith("user:"):
            yield Finding("GR003", r.address, "error",
                          f"{m} bound at {IAM_TYPES[r.type]} level; grant to a group instead")


# ---- GR004 WIF provider pinned to the GitHub org --------------------------------------------
GITHUB_ISSUER = "https://token.actions.githubusercontent.com"


@rule("GR004")
def wif_condition(r: Resource, policy: dict, ctx: dict):
    if r.type != "google_iam_workload_identity_pool_provider":
        return
    oidc = r.get("oidc")
    if oidc is UNKNOWN or not oidc:
        return
    issuer = (oidc[0] or {}).get("issuer_uri", "")
    if issuer.rstrip("/") != GITHUB_ISSUER:
        return
    cond = r.get("attribute_condition")
    owner = policy["github_owner"]
    if cond is UNKNOWN:
        yield unknown("GR004", r, "attribute_condition")
        return
    if not cond or not str(cond).strip():
        yield Finding("GR004", r.address, "error",
                      "GitHub OIDC provider has no attribute_condition: any repository on GitHub could federate")
        return
    q = r"['\"]"
    pins = [
        re.compile(r"assertion\.repository_owner\s*==\s*" + q + re.escape(owner) + q),
        re.compile(r"assertion\.repository_owner_id\s*==\s*" + q + r"\d+" + q),
        re.compile(r"assertion\.repository\s*==\s*" + q + re.escape(owner) + r"/[\w.-]+" + q),
    ]
    if not any(p.search(cond) for p in pins):
        yield Finding("GR004", r.address, "error",
                      f"attribute_condition does not pin assertion.repository_owner to '{owner}'")
    elif "||" in cond:
        yield Finding("GR004", r.address, "error",
                      "attribute_condition uses || which can bypass the owner check")


# ---- GR005 required org policies (cross-resource, checked once) -----------------------------
def _rules(r: Resource) -> list[dict]:
    spec = r.get("spec")
    if spec is UNKNOWN or not spec:
        return []
    return list((spec[0] or {}).get("rules") or [])


def _true(v: Any) -> bool:
    return str(v).upper() == "TRUE"


def check_org_policies(all_res: list[Resource], policy: dict) -> list[Finding]:
    org = f"organizations/{policy['org_id']}"
    have: dict[str, Resource] = {}
    for r in all_res:
        if r.type != "google_org_policy_policy":
            continue
        parent, name = r.get("parent"), r.get("name")
        if parent is UNKNOWN or name is UNKNOWN or parent != org:
            continue
        have[str(name).rsplit("/", 1)[-1]] = r
    req = policy.get("required_org_policies", {})
    out: list[Finding] = []
    where = f"{org} (org policies)"
    for c in req.get("boolean", []):
        r = have.get(c)
        if r is None:
            out.append(Finding("GR005", where, "error", f"required constraint {c} is not set at the organization"))
        elif not any(_true(x.get("enforce")) for x in _rules(r)):
            out.append(Finding("GR005", r.address, "error", f"{c} is present but not enforced"))
    for c in req.get("deny_all", []):
        r = have.get(c)
        if r is None:
            out.append(Finding("GR005", where, "error", f"required constraint {c} is not set at the organization"))
        elif not any(_true(x.get("deny_all")) for x in _rules(r)):
            out.append(Finding("GR005", r.address, "error", f"{c} must deny all values"))
    loc = req.get("locations")
    if loc:
        r = have.get(loc)
        if r is None:
            out.append(Finding("GR005", where, "error", f"required constraint {loc} is not set at the organization"))
        else:
            allowed = set(policy.get("allowed_regions", []))
            ok_vals = {f"in:{x}-locations" for x in allowed} | allowed | {f"zones:{x}" for x in allowed}
            vals: list[str] = []
            for x in _rules(r):
                for v in x.get("values") or []:
                    vals.extend(v.get("allowed_values") or [])
                if _true(x.get("allow_all")):
                    vals.append("ALLOW_ALL")
            if not vals:
                out.append(Finding("GR005", r.address, "error", f"{loc} has no allowed_values"))
            for v in vals:
                if v not in ok_vals:
                    out.append(Finding("GR005", r.address, "error", f"{loc} allows {v}, outside {sorted(allowed)}"))
    return out


# ---- GR006 subnets ---------------------------------------------------------------------------
@rule("GR006")
def subnet_regions(r: Resource, policy: dict, ctx: dict):
    if r.type != "google_compute_subnetwork":
        return
    region = r.get("region")
    if region is UNKNOWN:
        yield unknown("GR006", r, "region")
    elif region not in policy.get("allowed_regions", []):
        yield Finding("GR006", r.address, "error", f"subnet in {region}; allowed {policy['allowed_regions']}")
    pga = r.get("private_ip_google_access")
    if pga is not UNKNOWN and pga is not True:
        yield Finding("GR006", r.address, "error", "private_ip_google_access must be true")


# ---- GR007 buckets ---------------------------------------------------------------------------
@rule("GR007")
def buckets(r: Resource, policy: dict, ctx: dict):
    if r.type != "google_storage_bucket":
        return
    if r.get("uniform_bucket_level_access") is not True:
        yield Finding("GR007", r.address, "error", "uniform_bucket_level_access must be true")
    pap = r.get("public_access_prevention")
    if pap is not UNKNOWN and pap != "enforced":
        yield Finding("GR007", r.address, "error", "public_access_prevention must be \"enforced\"")
    loc = r.get("location")
    allowed = {x.upper() for x in policy.get("allowed_regions", [])} | {
        x.upper() for x in policy.get("extra_bucket_locations", [])}
    if loc is UNKNOWN:
        yield unknown("GR007", r, "location")
    elif str(loc).upper() not in allowed:
        yield Finding("GR007", r.address, "error", f"bucket location {loc} not allowed")


# ---- GR008 Shared VPC attachments (cross-resource) ------------------------------------------
def check_shared_vpc(all_res: list[Resource], policy: dict) -> list[Finding]:
    hosts = set()
    for r in all_res:
        if r.type == "google_compute_shared_vpc_host_project":
            p = r.get("project")
            if p is not UNKNOWN:
                hosts.add(p)
    attached: dict[str, str] = {}
    out: list[Finding] = []
    for r in all_res:
        if r.type != "google_compute_shared_vpc_service_project":
            continue
        host, svc = r.get("host_project"), r.get("service_project")
        if host is UNKNOWN or svc is UNKNOWN:
            out.append(unknown("GR008", r, "host_project/service_project"))
            if svc is not UNKNOWN:
                attached[svc] = r.address
            continue
        attached[svc] = r.address
        if host not in hosts:
            out.append(Finding("GR008", r.address, "error",
                               f"service project {svc} attaches to {host}, which is not a Shared VPC host"))
    for r in all_res:
        if r.type != "google_project":
            continue
        labels = r.get("labels") or {}
        if labels is UNKNOWN or labels.get("network") != "shared":
            continue
        pid = r.get("project_id")
        if pid is not UNKNOWN and pid not in attached:
            out.append(Finding("GR008", r.address, "error",
                               f"project {pid} is labelled network=shared but is not attached to a host project"))
    return out


# ---- GR009 no default network ---------------------------------------------------------------
@rule("GR009")
def no_default_network(r: Resource, policy: dict, ctx: dict):
    if r.type == "google_project" and r.get("auto_create_network") is not False:
        yield Finding("GR009", r.address, "error", "auto_create_network must be false (no default VPC)")


def evaluate(plan: dict, policy: dict) -> list[Finding]:
    all_res = list(resources(plan))
    out: list[Finding] = []
    ctx: dict = {}
    for r in all_res:
        for _, fn in RULES:
            out.extend(fn(r, policy, ctx))
    out.extend(check_org_policies(all_res, policy))
    out.extend(check_shared_vpc(all_res, policy))
    return sorted(set(out), key=lambda f: (f.rule, f.address, f.message))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("plan")
    ap.add_argument("--policy", default=str(Path(__file__).with_name("policy.yaml")))
    ap.add_argument("--json", action="store_true", help="print findings as a JSON array")
    args = ap.parse_args(argv)
    try:
        plan, policy = load_plan(args.plan), load_policy(args.policy)
    except (OSError, ValueError) as e:  # json.JSONDecodeError is a ValueError
        print(f"guardrails: {e}", file=sys.stderr)
        return 2
    findings = evaluate(plan, policy)
    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"{f.severity.upper():7} {f.rule} {f.address}: {f.message}")
        errs = sum(f.severity == "error" for f in findings)
        print(f"{len(findings)} finding(s), {errs} error(s)")
    return 1 if any(f.severity == "error" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
