#!/usr/bin/env python3
"""Local stand-in for Argo CD ApplicationSet rendering plus Helm chart version resolution.

It models what this incident needs and nothing more:

- Cluster generator: every Secret labelled argocd.argoproj.io/secret-type=cluster is a candidate;
  spec.generators[].clusters.selector filters them with matchLabels and matchExpressions
  (In, NotIn, Exists, DoesNotExist; Kubernetes label-selector semantics, so NotIn and
  DoesNotExist match clusters that do not have the key at all).
- Template parameters (fasttemplate style): {{name}}, {{server}}, {{metadata.labels.<key>}}.
- Helm targetRevision: an exact version or a semver constraint, resolved against the chart
  repository index.yaml the way Helm/Masterminds semver does: highest matching version wins;
  pre-releases (1.2.3-rc.1) are only considered when the constraint itself names a pre-release.
  Supported: "2.4.1", "2.*", "2.4.*", "~2.4", "^2.4", ">=2.0.0", "<3.0.0", "!=2.4.0", ranges
  joined by spaces or commas (AND) and alternatives joined by "||" (OR).

Usage:
  python tools/appset_sim.py [--appsets DIR] [--clusters DIR] [--index FILE] [--json]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$")


# ---------------------------------------------------------------------------- semver
def parse_version(s: str):
    m = SEMVER.match(str(s).strip())
    if not m:
        raise ValueError(f"not a semantic version: {s!r}")
    major, minor, patch, pre = m.groups()
    return (int(major), int(minor), int(patch), pre)


def _pre_key(pre):
    # A release sorts after any of its pre-releases.
    if pre is None:
        return (1, ())
    parts = []
    for p in pre.split("."):
        parts.append((0, int(p), "") if p.isdigit() else (1, 0, p))
    return (0, tuple(parts))


def vkey(v):
    return (v[0], v[1], v[2], _pre_key(v[3]))


def _partial(s: str):
    """Parse '2', '2.4', '2.4.1', '2.*', '2.4.x' -> (nums list, has_wildcard, pre)."""
    s = s.strip().lstrip("v")
    pre = None
    if "-" in s:
        s, pre = s.split("-", 1)
    parts = s.split(".")
    nums = []
    wild = False
    for p in parts:
        if p in ("*", "x", "X"):
            wild = True
            break
        nums.append(int(p))
    return nums, wild, pre


def _bounds_for(op: str, text: str):
    """Return a list of (cmp, version) primitive checks for one constraint term."""
    nums, wild, pre = _partial(text)
    full = lambda n: tuple(n + [0] * (3 - len(n)))  # noqa: E731
    if op in ("", "=") and (wild or len(nums) < 3):
        if not nums:
            return [], False
        lo = full(nums)
        hi = list(nums)
        hi[-1] += 1
        return [(">=", (*lo, None)), ("<", (*full(hi), "0"))], False
    if op == "~":
        lo = full(nums)
        if len(nums) >= 2:
            hi = [nums[0], nums[1] + 1]
        else:
            hi = [nums[0] + 1]
        return [(">=", (*lo, pre)), ("<", (*full(hi), "0"))], pre is not None
    if op == "^":
        lo = full(nums)
        if nums[0] > 0 or len(nums) == 1:
            hi = [nums[0] + 1]
        elif len(nums) > 1 and nums[1] > 0:
            hi = [0, nums[1] + 1]
        else:
            hi = [0, 0, (nums[2] if len(nums) > 2 else 0) + 1]
        return [(">=", (*lo, pre)), ("<", (*full(hi), "0"))], pre is not None
    v = (*full(nums), pre)
    return [(op or "=", v)], pre is not None


TERM = re.compile(r"(>=|<=|!=|>|<|=|~|\^)?\s*(v?[0-9xX*][0-9A-Za-z.*+-]*)")


def parse_constraint(c: str):
    """Return list of alternatives; each alternative is (checks, allows_prerelease)."""
    alts = []
    for alt in str(c).split("||"):
        checks, allow_pre = [], False
        text = alt.replace(",", " ").strip()
        if not text:
            raise ValueError(f"empty constraint in {c!r}")
        pos = 0
        while pos < len(text):
            if text[pos].isspace():
                pos += 1
                continue
            m = TERM.match(text, pos)
            if not m:
                raise ValueError(f"cannot parse constraint {c!r} at {text[pos:]!r}")
            op, ver = m.group(1) or "", m.group(2)
            ch, pre = _bounds_for(op, ver)
            checks.extend(ch)
            allow_pre = allow_pre or pre
            pos = m.end()
        alts.append((checks, allow_pre))
    return alts


def _cmp(op, v, ref):
    a, b = vkey(v), vkey(ref)
    return {"=": a == b, "!=": a != b, ">": a > b, ">=": a >= b, "<": a < b, "<=": a <= b}[op]


def satisfies(version: str, constraint: str) -> bool:
    v = parse_version(version)
    for checks, allow_pre in parse_constraint(constraint):
        if v[3] is not None and not allow_pre:
            continue
        if all(_cmp(op, v, ref) for op, ref in checks):
            return True
    return False


def resolve(constraint: str, versions: list[str]) -> str:
    """Highest version in `versions` that satisfies `constraint` (exact strings match exactly)."""
    c = str(constraint).strip()
    if SEMVER.match(c):
        if c.lstrip("v") in [x.lstrip("v") for x in versions]:
            return c.lstrip("v")
        raise LookupError(f"chart version {c} not found in index")
    ok = [x for x in versions if SEMVER.match(x) and satisfies(x, c)]
    if not ok:
        raise LookupError(f"no chart version satisfies {c!r}")
    return max(ok, key=lambda x: vkey(parse_version(x)))


# ------------------------------------------------------------------------ argo model
def load_yaml_docs(directory: pathlib.Path) -> list[dict]:
    docs = []
    for p in sorted(directory.glob("*.yaml")):
        for d in yaml.safe_load_all(p.read_text()):
            if d:
                d["__file"] = p.name
                docs.append(d)
    return docs


def load_clusters(directory: pathlib.Path) -> list[dict]:
    out = []
    for d in load_yaml_docs(directory):
        meta = d.get("metadata") or {}
        labels = meta.get("labels") or {}
        if d.get("kind") != "Secret" or labels.get("argocd.argoproj.io/secret-type") != "cluster":
            continue
        data = d.get("stringData") or {}
        out.append({"name": data.get("name"), "server": data.get("server"),
                    "labels": {k: str(v) for k, v in labels.items()}})
    return out


def selector_matches(selector: dict | None, labels: dict) -> bool:
    selector = selector or {}
    for k, v in (selector.get("matchLabels") or {}).items():
        if labels.get(k) != str(v):
            return False
    for e in selector.get("matchExpressions") or []:
        key, op, vals = e["key"], e["operator"], [str(x) for x in e.get("values") or []]
        has = key in labels
        if op == "In" and not (has and labels[key] in vals):
            return False
        if op == "NotIn" and has and labels[key] in vals:
            return False
        if op == "Exists" and not has:
            return False
        if op == "DoesNotExist" and has:
            return False
        if op not in ("In", "NotIn", "Exists", "DoesNotExist"):
            raise ValueError(f"unsupported selector operator {op}")
    return True


PARAM = re.compile(r"\{\{\s*([A-Za-z0-9_.\-/]+)\s*\}\}")


def substitute(value, params: dict):
    if isinstance(value, str):
        def rep(m):
            k = m.group(1)
            if k not in params:
                raise KeyError(f"unknown template parameter {{{{{k}}}}}")
            return params[k]
        return PARAM.sub(rep, value)
    if isinstance(value, list):
        return [substitute(v, params) for v in value]
    if isinstance(value, dict):
        return {k: substitute(v, params) for k, v in value.items()}
    return value


def render(appsets_dir, clusters_dir, index_path) -> list[dict]:
    """Return one row per generated Application."""
    appsets_dir, clusters_dir, index_path = map(pathlib.Path, (appsets_dir, clusters_dir, index_path))
    clusters = load_clusters(clusters_dir)
    index = yaml.safe_load(index_path.read_text())
    rows = []
    for aset in load_yaml_docs(appsets_dir):
        if aset.get("kind") != "ApplicationSet":
            continue
        aname = aset["metadata"]["name"]
        for gen in aset["spec"].get("generators") or []:
            if "clusters" not in gen:
                raise ValueError(f"{aname}: only the clusters generator is modeled")
            sel = (gen["clusters"] or {}).get("selector")
            for c in clusters:
                if not selector_matches(sel, c["labels"]):
                    continue
                params = {"name": c["name"], "server": c["server"]}
                for k, v in c["labels"].items():
                    params[f"metadata.labels.{k}"] = v
                tpl = substitute(aset["spec"]["template"], params)
                src = tpl["spec"]["source"]
                chart = src["chart"]
                versions = [e["version"] for e in index["entries"].get(chart, [])]
                try:
                    resolved = resolve(src["targetRevision"], versions)
                except (LookupError, ValueError) as e:
                    resolved = f"ERROR: {e}"
                rows.append({
                    "cluster": c["name"],
                    "applicationset": aname,
                    "application": tpl["metadata"]["name"],
                    "chart": chart,
                    "targetRevision": str(src["targetRevision"]),
                    "resolved": resolved,
                    "valueFiles": (src.get("helm") or {}).get("valueFiles", []),
                    "automated": bool(((tpl["spec"].get("syncPolicy") or {}).get("automated"))),
                })
    return sorted(rows, key=lambda r: (r["cluster"], r["applicationset"]))


def coverage(rows: list[dict], clusters_dir) -> dict:
    names = [c["name"] for c in load_clusters(pathlib.Path(clusters_dir))]
    count = {n: 0 for n in names}
    for r in rows:
        count[r["cluster"]] = count.get(r["cluster"], 0) + 1
    return count


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--appsets", default=str(ROOT / "argocd" / "applicationsets"))
    ap.add_argument("--clusters", default=str(ROOT / "argocd" / "clusters"))
    ap.add_argument("--index", default=str(ROOT / "charts" / "index.yaml"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = render(a.appsets, a.clusters, a.index)
    cov = coverage(rows, a.clusters)
    if a.json:
        print(json.dumps({"applications": rows, "coverage": cov}, indent=2))
        return 0
    print(f"{'cluster':<12} {'applicationset':<16} {'application':<22} {'targetRevision':<16} {'resolved':<10} automated")
    for r in rows:
        print(f"{r['cluster']:<12} {r['applicationset']:<16} {r['application']:<22} {r['targetRevision']:<16} {r['resolved']:<10} {r['automated']}")
    for n, k in sorted(cov.items()):
        if k != 1:
            print(f"WARNING cluster {n} is targeted by {k} ApplicationSets (want exactly 1)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
