#!/usr/bin/env python3
"""Node drain simulator for a GKE surge upgrade (local stand-in for kubectl drain + the Eviction API).

Inputs:
  k8s/**/*.yaml        rendered manifests (Deployments, StatefulSets, PodDisruptionBudgets); the pod
                       labels and controller scale come from here
  cluster/state.json   nodes in upgrade order and the pods currently running on them, with readiness

For every node to upgrade, in order, it evicts each pod the way the Eviction API does:
  - every PDB whose selector matches the pod is evaluated:
      minAvailable N (int or %)   desiredHealthy = N (percent of expected, rounded up)
      maxUnavailable M (int or %) desiredHealthy = expected - M (percent of expected, rounded up)
    expected = sum of the scale (replicas) of the controllers that own the matching pods
    currentHealthy = matching pods that are Ready
    disruptionsAllowed = max(0, currentHealthy - desiredHealthy)
  - a Ready pod is evicted only if disruptionsAllowed > 0 for every matching PDB
  - a pod that is not Ready is evicted if unhealthyPodEvictionPolicy is AlwaysAllow, or (default
    IfHealthyBudget) if currentHealthy >= desiredHealthy
  - an evicted pod is recreated on an upgraded node; it is Ready again unless its controller is listed
    in state.json "broken_controllers" (for example a crash-looping image)
A node that cannot be drained stops the upgrade there, the way the GKE node pool upgrade waits on it.

Usage: python tools/drain_sim.py [--k8s k8s] [--state cluster/state.json] [--json]
Exit 0 when every node drains, 1 when the upgrade is stuck, 2 on bad input.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import yaml


def load_manifests(root: str | Path) -> list[dict]:
    docs = []
    for p in sorted(Path(root).rglob("*.yaml")):
        for d in yaml.safe_load_all(p.read_text()):
            if isinstance(d, dict) and d.get("kind"):
                docs.append(d)
    return docs


def matches(selector: dict | None, labels: dict) -> bool:
    if not selector:
        return False  # an empty PDB selector matches nothing in this model
    for k, v in (selector.get("matchLabels") or {}).items():
        if labels.get(k) != v:
            return False
    for e in selector.get("matchExpressions") or []:
        k, op, vals = e["key"], e["operator"], e.get("values") or []
        if op == "In" and labels.get(k) not in vals:
            return False
        if op == "NotIn" and k in labels and labels[k] in vals:
            return False
        if op == "Exists" and k not in labels:
            return False
        if op == "DoesNotExist" and k in labels:
            return False
    return True


def _scaled(value, expected: int) -> int:
    if isinstance(value, str) and value.endswith("%"):
        return math.ceil(expected * int(value[:-1]) / 100)
    return int(value)


class Cluster:
    def __init__(self, docs: list[dict], state: dict):
        self.controllers = {}
        for d in docs:
            if d["kind"] in ("Deployment", "StatefulSet"):
                ns = d["metadata"].get("namespace", "default")
                self.controllers[(ns, d["metadata"]["name"])] = {
                    "replicas": int(d["spec"].get("replicas", 1)),
                    "labels": dict(d["spec"]["template"]["metadata"].get("labels") or {}),
                }
        self.pdbs = [d for d in docs if d["kind"] == "PodDisruptionBudget"]
        self.broken = set(state.get("broken_controllers", []))
        self.nodes = state["nodes"]
        self.pods = []
        for p in state["pods"]:
            key = (p["namespace"], p["controller"])
            if key not in self.controllers:
                continue  # controller removed from the manifests: its pods are gone
            self.pods.append({**p, "labels": self.controllers[key]["labels"]})

    def pdb_status(self, pdb: dict) -> dict:
        ns = pdb["metadata"].get("namespace", "default")
        sel = pdb["spec"].get("selector")
        pods = [p for p in self.pods if p["namespace"] == ns and matches(sel, p["labels"])]
        owners = {(p["namespace"], p["controller"]) for p in pods}
        expected = sum(self.controllers[o]["replicas"] for o in owners)
        healthy = sum(1 for p in pods if p["ready"])
        spec = pdb["spec"]
        if "minAvailable" in spec:
            desired = _scaled(spec["minAvailable"], expected)
        elif "maxUnavailable" in spec:
            desired = expected - _scaled(spec["maxUnavailable"], expected)
        else:
            desired = 0
        return {"name": f"{ns}/{pdb['metadata']['name']}", "expected": expected, "currentHealthy": healthy,
                "desiredHealthy": desired, "disruptionsAllowed": max(0, healthy - desired),
                "policy": spec.get("unhealthyPodEvictionPolicy", "IfHealthyBudget"), "pods": len(pods)}

    def evict(self, pod: dict) -> tuple[bool, str]:
        for pdb in self.pdbs:
            ns = pdb["metadata"].get("namespace", "default")
            if ns != pod["namespace"] or not matches(pdb["spec"].get("selector"), pod["labels"]):
                continue
            st = self.pdb_status(pdb)
            if pod["ready"]:
                if st["disruptionsAllowed"] <= 0:
                    return False, (f"Cannot evict pod as it would violate the pod's disruption budget "
                                   f"({st['name']}: expected {st['expected']}, healthy {st['currentHealthy']}, "
                                   f"desired {st['desiredHealthy']}, allowed 0)")
            else:
                if st["policy"] != "AlwaysAllow" and st["currentHealthy"] < st["desiredHealthy"]:
                    return False, f"Cannot evict unready pod: {st['name']} is below desiredHealthy"
        return True, "evicted"

    def drain_all(self) -> list[dict]:
        out = []
        for node in self.nodes:
            if node.get("upgraded"):
                continue
            events, stuck = [], False
            for pod in [p for p in self.pods if p["node"] == node["name"]]:
                ok, msg = self.evict(pod)
                events.append(f"{pod['namespace']}/{pod['name']}: {msg}")
                if not ok:
                    stuck = True
                    break
                pod["node"] = "upgraded-pool"
                pod["ready"] = f"{pod['namespace']}/{pod['controller']}" not in self.broken
            out.append({"node": node["name"], "drained": not stuck, "events": events})
            if stuck:
                break
            node["upgraded"] = True
        return out


def run(k8s: str | Path, state_path: str | Path) -> dict:
    docs = load_manifests(k8s)
    state = json.loads(Path(state_path).read_text())
    c = Cluster(docs, state)
    before = [c.pdb_status(p) for p in c.pdbs]
    nodes = c.drain_all()
    pending = [n["name"] for n in state["nodes"] if not n.get("upgraded")]
    return {"pdbs_before": before, "nodes": nodes, "complete": not pending, "pending": pending}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="drain simulator")
    here = Path(__file__).resolve().parents[1]
    ap.add_argument("--k8s", default=str(here / "k8s"))
    ap.add_argument("--state", default=str(here / "cluster" / "state.json"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        res = run(args.k8s, args.state)
    except (OSError, ValueError, KeyError, yaml.YAMLError) as e:
        print(f"drain_sim: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print("PDBs before the drain:")
        for s in res["pdbs_before"]:
            print(f"  {s['name']:18} pods={s['pods']} expected={s['expected']} healthy={s['currentHealthy']} "
                  f"desired={s['desiredHealthy']} allowed={s['disruptionsAllowed']}")
        for n in res["nodes"]:
            print(f"{'DRAINED' if n['drained'] else 'STUCK  '} {n['node']}")
            for e in n["events"]:
                print(f"    {e}")
        print("upgrade complete" if res["complete"] else f"upgrade stuck, {len(res['pending'])} node(s) pending")
    return 0 if res["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
