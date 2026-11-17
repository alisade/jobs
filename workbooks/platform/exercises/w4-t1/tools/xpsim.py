#!/usr/bin/env python3
"""Local Crossplane v2 stand-in: renders AppDatabase XRs through the platform Composition and simulates
what the provider does with the composed managed resources (MRs).

Model (a deliberately small subset of Crossplane v2 and the Upjet GCP provider family):
  - XRD apiextensions.crossplane.io/v2, scope Namespaced. XRs live in team namespaces; there are no claims.
  - Composition mode Pipeline with one step using function-patch-and-transform. Each resource has a
    `base` and `patches` of type FromCompositeFieldPath (fromFieldPath -> toFieldPath, optional
    transforms: map, string Format) and ToCompositeFieldPath is ignored here.
  - Composed MRs are namespaced and created in the XR's namespace.
  - Provider: an MR's spec.providerConfigRef {kind, name}; kind defaults to "ProviderConfig".
      ProviderConfig        is namespaced: looked up in the MR's own namespace
      ClusterProviderConfig is cluster-scoped
    A missing config gives Synced=False, ReconcileError "cannot get referenced ProviderConfig".
    A found config with credentials.source InjectedIdentity (Workload Identity) is usable.
  - XR Ready=True only when every composed MR is Ready.

Inputs: platform/*.yaml (XRD, Composition, provider configs), teams/**/*.yaml (XRs).
Usage: python tools/xpsim.py [--json]     exit 0 if every XR is Ready, 1 otherwise, 2 on bad input
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(dirs) -> list[dict]:
    out = []
    for d in dirs:
        for p in sorted(Path(d).rglob("*.yaml")):
            out += [x for x in yaml.safe_load_all(p.read_text()) if isinstance(x, dict) and x.get("kind")]
    return out


def get_path(obj, path: str):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        elif isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def set_path(obj, path: str, value):
    parts = path.split(".")
    cur = obj
    for i, part in enumerate(parts[:-1]):
        nxt_is_index = parts[i + 1].isdigit()
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur.setdefault(part, [{}] if nxt_is_index else {})
    last = parts[-1]
    if isinstance(cur, list):
        cur[int(last)] = value
    else:
        cur[last] = value


def transform(value, transforms):
    for t in transforms or []:
        if t["type"] == "map":
            if value not in t["map"]:
                raise ValueError(f"map transform has no key {value!r}")
            value = t["map"][value]
        elif t["type"] == "string" and t["string"].get("type") == "Format":
            value = t["string"]["fmt"] % value
        else:
            raise ValueError(f"unsupported transform {t}")
    return value


def render(xr: dict, comp: dict) -> list[dict]:
    steps = comp["spec"]["pipeline"]
    out = []
    for step in steps:
        if step["functionRef"]["name"] != "function-patch-and-transform":
            raise ValueError(f"unsupported function {step['functionRef']['name']}")
        for res in step["input"]["resources"]:
            mr = copy.deepcopy(res["base"])
            for p in res.get("patches", []):
                if p.get("type", "FromCompositeFieldPath") != "FromCompositeFieldPath":
                    continue
                v = get_path(xr, p["fromFieldPath"])
                if v is None:
                    continue
                set_path(mr, p["toFieldPath"], transform(v, p.get("transforms")))
            mr.setdefault("metadata", {})
            mr["metadata"]["namespace"] = xr["metadata"]["namespace"]
            mr["metadata"].setdefault("name", f"{xr['metadata']['name']}-{res['name']}")
            mr["metadata"].setdefault("labels", {})["crossplane.io/composite"] = xr["metadata"]["name"]
            mr["_resource"] = res["name"]
            out.append(mr)
    return out


def provider_status(mr: dict, configs: list[dict]) -> dict:
    ref = (mr.get("spec") or {}).get("providerConfigRef") or {"name": "default"}
    kind = ref.get("kind", "ProviderConfig")
    name = ref.get("name", "default")
    ns = mr["metadata"]["namespace"]
    found = None
    for c in configs:
        if c["kind"] != kind or c["metadata"]["name"] != name:
            continue
        if kind == "ProviderConfig" and c["metadata"].get("namespace") != ns:
            continue
        found = c
    if not found:
        where = f"namespace {ns}" if kind == "ProviderConfig" else "cluster scope"
        return {"Synced": False, "Ready": False, "reason": "ReconcileError",
                "message": f"cannot get referenced ProviderConfig: {kind}.gcp.m.upbound.io \"{name}\" not found in {where}"}
    src = (found["spec"].get("credentials") or {}).get("source")
    if src not in ("InjectedIdentity", "Secret"):
        return {"Synced": False, "Ready": False, "reason": "ReconcileError", "message": f"unsupported credentials source {src}"}
    return {"Synced": True, "Ready": True, "reason": "Available", "message": ""}


def run(platform_dir=ROOT / "platform", teams_dir=ROOT / "teams") -> dict:
    docs = load([platform_dir, teams_dir])
    xrd = next(d for d in docs if d["kind"] == "CompositeResourceDefinition")
    if xrd["spec"].get("scope", "Namespaced") != "Namespaced":
        raise ValueError("this platform only supports namespaced XRs (Crossplane v2)")
    comp = next(d for d in docs if d["kind"] == "Composition")
    configs = [d for d in docs if d["kind"] in ("ProviderConfig", "ClusterProviderConfig")]
    xr_kind = xrd["spec"]["names"]["kind"]
    results = []
    for xr in [d for d in docs if d["kind"] == xr_kind]:
        if "namespace" not in xr["metadata"]:
            raise ValueError(f"XR {xr['metadata']['name']} has no namespace")
        try:
            mrs = render(xr, comp)
        except ValueError as e:
            results.append({"xr": f"{xr['metadata']['namespace']}/{xr['metadata']['name']}", "Ready": False,
                            "message": f"composition failed: {e}", "resources": []})
            continue
        rs = []
        for mr in mrs:
            st = provider_status(mr, configs)
            rs.append({"kind": mr["kind"], "name": mr["metadata"]["name"], "namespace": mr["metadata"]["namespace"],
                       "spec": mr.get("spec", {}), **st})
        not_ready = [r["name"] for r in rs if not r["Ready"]]
        results.append({"xr": f"{xr['metadata']['namespace']}/{xr['metadata']['name']}", "Ready": not not_ready,
                        "message": "" if not not_ready else "Unready resources: " + ", ".join(not_ready),
                        "resources": rs})
    return {"xrs": results}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", default=str(ROOT / "platform"))
    ap.add_argument("--teams", default=str(ROOT / "teams"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = run(a.platform, a.teams)
    except (OSError, ValueError, KeyError, StopIteration, yaml.YAMLError) as e:
        print(f"xpsim: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        for x in res["xrs"]:
            print(f"{'READY  ' if x['Ready'] else 'NOT READY'} {x['xr']}  {x['message']}")
            for r in x["resources"]:
                print(f"    {r['kind']:18} {r['name']:28} Synced={r['Synced']} Ready={r['Ready']} {r['message']}")
    return 0 if all(x["Ready"] for x in res["xrs"]) else 1


if __name__ == "__main__":
    sys.exit(main())
