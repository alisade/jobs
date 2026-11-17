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
    # TODO: IAM resources in IAM_TYPES granting a role listed in policy["basic_roles"] are errors.
    #       An UNKNOWN role is a warning (use unknown()).
    return
    yield


@rule("GR003")
def no_users_high_in_tree(r: Resource, policy: dict, ctx: dict):
    # TODO: "user:" principals bound on an organization or a folder are errors (bind groups).
    #       iam_members() already handles _member vs _binding resources.
    return
    yield


# ---- GR004 WIF provider pinned to the GitHub org --------------------------------------------
GITHUB_ISSUER = "https://token.actions.githubusercontent.com"


@rule("GR004")
def wif_condition(r: Resource, policy: dict, ctx: dict):
    # TODO: for google_iam_workload_identity_pool_provider with the GitHub OIDC issuer
    #       (GITHUB_ISSUER), require an attribute_condition that pins the GitHub org: see README.
    return
    yield


# ---- GR005 required org policies (cross-resource, checked once) -----------------------------
def _rules(r: Resource) -> list[dict]:
    spec = r.get("spec")
    if spec is UNKNOWN or not spec:
        return []
    return list((spec[0] or {}).get("rules") or [])


def _true(v: Any) -> bool:
    return str(v).upper() == "TRUE"


def check_org_policies(all_res: list[Resource], policy: dict) -> list[Finding]:
    # TODO: GR005. Look at google_org_policy_policy resources whose parent is the organization and
    #       check policy["required_org_policies"]: boolean (enforce TRUE), deny_all (deny_all TRUE),
    #       locations (every allowed value inside policy["allowed_regions"]). See README for shapes.
    return []


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
    # TODO: uniform bucket-level access, public access prevention "enforced", allowed location.
    return
    yield


# ---- GR008 Shared VPC attachments (cross-resource) ------------------------------------------
def check_shared_vpc(all_res: list[Resource], policy: dict) -> list[Finding]:
    # TODO: GR008. Service project attachments must point at a declared host project, and every
    #       google_project labelled network=shared must be attached.
    return []


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
