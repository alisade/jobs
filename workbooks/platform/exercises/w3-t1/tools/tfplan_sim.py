#!/usr/bin/env python3
"""A local stand-in for `terraform plan` on an import batch (no provider download, no GCP).

Reads the root module in migration/*.tf (HCL, parsed with python-hcl2), the live objects in
live/inventory.json (keyed by import ID, as the provider would read them) and a mini provider schema
in schema/google-mini.json (per attribute: default, force_new, computed).

For each resource block:
  - with an import block (`to` = its address): the live object is read by import ID, then the config is
    compared with it attribute by attribute. An attribute missing from the config takes the schema
    default (or, when computed, keeps the live value). A difference on a force_new attribute means
    "must be replaced"; any other difference is an in-place update; none is a pure import.
  - without an import block: create.
  - lifecycle { prevent_destroy = true } on a resource that would be replaced is a plan error, as in
    Terraform ("Instance cannot be destroyed").
References like google_compute_network.core.id resolve to the referenced resource's import ID.

Usage: python tools/tfplan_sim.py [--dir migration] [--live live/inventory.json] [--json]
Exit 0 for a plan with no changes besides imports, 1 for a plan with changes, 2 for a plan error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import hcl2

ROOT = Path(__file__).resolve().parents[1]
REF = re.compile(r"^\$\{([a-z0-9_]+\.[a-z0-9_]+)\.(id|self_link|name)\}$")


class PlanError(Exception):
    pass


def load_config(d: Path) -> tuple[dict, dict]:
    resources, imports = {}, {}
    for p in sorted(Path(d).glob("*.tf")):
        doc = hcl2.loads(p.read_text())
        for imp in doc.get("import", []):
            to = imp["to"]
            to = to[2:-1] if to.startswith("${") else to
            imports[to] = imp["id"]
        for block in doc.get("resource", []):
            for rtype, named in block.items():
                for name, body in named.items():
                    resources[f"{rtype}.{name}"] = {"type": rtype, "body": body}
    return resources, imports


def get(obj, path):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[0] if cur else None
        if not isinstance(cur, dict) or part not in cur:
            return None, False
        cur = cur[part]
    return cur, True


def resolve(v, imports):
    if isinstance(v, str):
        m = REF.match(v)
        if m:
            target = m.group(1)
            if target not in imports:
                raise PlanError(f"reference to {target} which has no import ID in this batch")
            return imports[target] if m.group(2) != "name" else imports[target].rsplit("/", 1)[-1]
    return v


def plan(d=ROOT / "migration", live_path=ROOT / "live" / "inventory.json", schema_path=ROOT / "schema" / "google-mini.json") -> dict:
    resources, imports = load_config(Path(d))
    live = json.loads(Path(live_path).read_text())
    schema = json.loads(Path(schema_path).read_text())
    for to in imports:
        if to not in resources:
            raise PlanError(f"import block targets {to}, which has no resource block")
    changes = []
    for addr, r in sorted(resources.items()):
        sch = schema.get(r["type"])
        if sch is None:
            raise PlanError(f"{r['type']} is not in the mini provider schema")
        lifecycle = (r["body"].get("lifecycle") or [{}])[0]
        if addr not in imports:
            changes.append({"address": addr, "action": "create", "importing": None, "diffs": []})
            continue
        iid = imports[addr]
        obj = live.get(iid)
        if obj is None or obj["type"] != r["type"]:
            raise PlanError(f"Cannot import non-existent remote object: {addr} id {iid}")
        diffs = []
        for attr, spec in sch.items():
            cval, present = get(r["body"], attr)
            lval, _ = get(obj["attrs"], attr)
            if not present:
                if spec.get("computed"):
                    continue
                cval = spec.get("default")
            cval = resolve(cval, imports)
            if cval != lval:
                diffs.append({"attr": attr, "live": lval, "config": cval, "force_new": bool(spec.get("force_new"))})
        if any(x["force_new"] for x in diffs):
            if lifecycle.get("prevent_destroy") is True:
                raise PlanError(f"Instance cannot be destroyed: {addr} has lifecycle.prevent_destroy set, "
                                f"but the plan calls for this resource to be destroyed (forced by "
                                f"{', '.join(x['attr'] for x in diffs if x['force_new'])})")
            action = "replace"
        elif diffs:
            action = "update"
        else:
            action = "no-op"
        changes.append({"address": addr, "action": action, "importing": iid, "diffs": diffs})
    s = {"import": sum(1 for c in changes if c["importing"]),
         "add": sum(1 for c in changes if c["action"] in ("create", "replace")),
         "change": sum(1 for c in changes if c["action"] == "update"),
         "destroy": sum(1 for c in changes if c["action"] == "replace")}
    return {"changes": changes, "summary": s}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "migration"))
    ap.add_argument("--live", default=str(ROOT / "live" / "inventory.json"))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        res = plan(a.dir, a.live)
    except PlanError as e:
        print(f"Error: {e}")
        return 2
    if a.json:
        print(json.dumps(res, indent=2))
        return 0
    sym = {"no-op": "  ", "update": " ~", "replace": "-/+", "create": " +"}
    for c in res["changes"]:
        what = {"no-op": "will be imported", "update": "will be imported and updated in-place",
                "replace": "must be replaced", "create": "will be created"}[c["action"]]
        print(f"  # {c['address']} {what}")
        for d in c["diffs"]:
            note = " # forces replacement" if d["force_new"] else ""
            print(f"  {sym[c['action']]} {d['attr']} = {json.dumps(d['live'])} -> {json.dumps(d['config'])}{note}")
    s = res["summary"]
    print(f"\nPlan: {s['import']} to import, {s['add']} to add, {s['change']} to change, {s['destroy']} to destroy.")
    return 0 if not (s["add"] or s["change"] or s["destroy"]) else 1


if __name__ == "__main__":
    sys.exit(main())
