#!/usr/bin/env python3
"""remediate.py: Corvane AppSec remediation report.

Compares the CycloneDX SBOM from before an upgrade with the one after it, against the offline
advisory mirror (OSV format, Maven ecosystem), and writes the report AppSec signs off on.

Usage: remediate.py --before sbom/before.cdx.json --after sbom/after.cdx.json \
                    --advisories advisories --out report [--fail-on CRITICAL]

Statuses per (advisory, package):
  fixed         affected before, not affected after
  remaining     affected before and after
  introduced    not affected (or absent) before, affected after
  not-affected  affected in neither
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def parse_sbom(path: Path) -> dict[str, str]:
    """Return {"group:artifact": version} for every library component."""
    bom = json.loads(Path(path).read_text())
    out = {}
    for c in bom.get("components", []):
        if c.get("type") == "library":
            out[f"{c['group']}:{c['name']}"] = c["version"]
    return out


def load_advisories(directory: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(Path(directory).glob("*.json"))]


# Maven-style ordering of qualifiers (close to org.apache.maven.artifact.versioning.ComparableVersion):
# alpha < beta < milestone < rc/cr < snapshot < release ("", ga, final, release) < sp < anything unknown.
_QUALIFIER_RANK = {"alpha": 0, "a": 0, "beta": 1, "b": 1, "milestone": 2, "m": 2, "rc": 3, "cr": 3,
                   "snapshot": 4, "": 5, "ga": 5, "final": 5, "release": 5, "sp": 6}


def _key(v: str) -> tuple:
    """Sort key: numeric release part (trailing zeros ignored), then the qualifier."""
    import re
    v = v.strip().lower()
    m = re.match(r"^(\d+(?:\.\d+)*)(.*)$", v)
    if not m:
        return ((), 5, 0, v)
    nums = [int(x) for x in m.group(1).split(".")]
    while nums and nums[-1] == 0:
        nums.pop()
    rest = m.group(2).lstrip(".-_")
    q = re.match(r"^([a-z]*)[.\-_]?(\d*)(.*)$", rest)
    word, qnum, tail = q.group(1), q.group(2), q.group(3)
    rank = _QUALIFIER_RANK.get(word, 7)
    return (tuple(nums), rank, int(qnum) if qnum else 0, word if rank == 7 else "", tail)


def compare_versions(a: str, b: str) -> int:
    """Negative if a < b, zero if equal, positive if a > b, by version semantics, not by string."""
    ka, kb = _key(a), _key(b)
    return (ka > kb) - (ka < kb)


def is_affected(version: str, ranges: list[dict]) -> bool:
    """True when version falls in any [introduced, fixed) range of the advisory."""
    for r in ranges:
        introduced, fixed = "0", None
        for e in r.get("events", []):
            introduced = e.get("introduced", introduced)
            fixed = e.get("fixed", fixed)
        lower_ok = introduced == "0" or compare_versions(version, introduced) >= 0
        upper_ok = fixed is None or compare_versions(version, fixed) < 0
        if lower_ok and upper_ok:
            return True
    return False


def build_report(before: dict[str, str], after: dict[str, str], advisories: list[dict]) -> dict:
    findings = []
    for adv in advisories:
        sev = adv.get("database_specific", {}).get("severity", "LOW").upper()
        for aff in adv.get("affected", []):
            pkg = aff["package"]["name"]
            if pkg not in before and pkg not in after:
                continue
            b, a = before.get(pkg), after.get(pkg)
            hit_b = b is not None and is_affected(b, aff.get("ranges", []))
            hit_a = a is not None and is_affected(a, aff.get("ranges", []))
            if hit_b and not hit_a:
                status = "fixed"
            elif hit_b and hit_a:
                status = "remaining"
            elif hit_a:
                status = "introduced"
            else:
                status = "not-affected"
            findings.append({"advisory": adv["id"], "package": pkg, "severity": sev,
                             "before": b, "after": a, "status": status})
    open_items = [f for f in findings if f["status"] in ("remaining", "introduced")]
    summary = {
        "fixed": sum(1 for f in findings if f["status"] == "fixed"),
        "remaining": sum(1 for f in findings if f["status"] == "remaining"),
        "introduced": sum(1 for f in findings if f["status"] == "introduced"),
        "open_by_severity": {s: sum(1 for f in open_items if f["severity"] == s) for s in reversed(SEVERITY_ORDER)},
    }
    return {"summary": summary, "findings": findings}


def to_markdown(report: dict, generated: str) -> str:
    s = report["summary"]
    lines = [f"# Remediation report ({generated})", "",
             f"Fixed: {s['fixed']}  Remaining: {s['remaining']}  Introduced: {s['introduced']}", "",
             "Open by severity: " + ", ".join(f"{k} {v}" for k, v in s["open_by_severity"].items()), "",
             "| Advisory | Package | Severity | Before | After | Status |", "|---|---|---|---|---|---|"]
    for f in report["findings"]:
        lines.append(f"| {f['advisory']} | {f['package']} | {f['severity']} | {f['before']} | {f['after']} | {f['status']} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", type=Path, required=True)
    ap.add_argument("--after", type=Path, required=True)
    ap.add_argument("--advisories", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--fail-on", default=None, help="exit 1 when an open finding is at or above this severity")
    args = ap.parse_args(argv)
    report = build_report(parse_sbom(args.before), parse_sbom(args.after), load_advisories(args.advisories))
    args.out.mkdir(parents=True, exist_ok=True)
    generated = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "report.md").write_text(to_markdown(report, generated))
    print(json.dumps(report["summary"]))
    if args.fail_on:
        floor = SEVERITY_ORDER.index(args.fail_on.upper())
        if any(f["status"] in ("remaining", "introduced") and SEVERITY_ORDER.index(f["severity"]) >= floor
               for f in report["findings"]):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
