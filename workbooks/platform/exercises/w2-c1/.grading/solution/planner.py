#!/usr/bin/env python3
"""Fleet upgrade planner for Tessellate's GKE fleet.

Reads a fleet state file (fleet.json) and prints an ordered, window-aware upgrade plan to the target
GKE version, or the reasons a cluster cannot be upgraded yet. It plans; it never calls GKE.

Usage: python planner.py fleet.json [--json]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)-gke\.(\d+)$")
DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
HORIZON_DAYS = 90


# ------------------------------------------------------------------ helpers (given)
def parse_version(v: str) -> tuple[int, int, int, int]:
    m = VERSION.match(v)
    if not m:
        raise ValueError(f"not a GKE version: {v!r}")
    return tuple(int(x) for x in m.groups())  # type: ignore[return-value]


def minor(v: str) -> tuple[int, int]:
    p = parse_version(v)
    return (p[0], p[1])


def ts(s: str) -> dt.datetime:
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso(d: dt.datetime) -> str:
    return d.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def window_occurrences(window: dict, after: dt.datetime, days: int = HORIZON_DAYS):
    """Yield (start, end) of each maintenance window occurrence starting at or after `after`.

    window = {"days": ["TU","WE"], "start": "03:00", "duration_hours": 4} in UTC.
    """
    hh, mm = (int(x) for x in window["start"].split(":"))
    dur = dt.timedelta(hours=window["duration_hours"])
    day0 = after.replace(hour=0, minute=0, second=0, microsecond=0)
    for i in range(days + 1):
        d = day0 + dt.timedelta(days=i)
        if DAYS[d.weekday()] not in window["days"]:
            continue
        start = d.replace(hour=hh, minute=mm)
        if start >= after:
            yield start, start + dur


# ------------------------------------------------------------------ the planner
BLOCKING_SCOPES = {
    # (component, is_minor) -> exclusion scopes that block it
    ("control_plane", True): {"NO_UPGRADES", "NO_MINOR_UPGRADES", "NO_MINOR_OR_NODE_UPGRADES"},
    ("control_plane", False): {"NO_UPGRADES"},
    ("node_pool", True): {"NO_UPGRADES", "NO_MINOR_UPGRADES", "NO_MINOR_OR_NODE_UPGRADES"},
    ("node_pool", False): {"NO_UPGRADES", "NO_MINOR_OR_NODE_UPGRADES"},
}


def best_in_minor(versions: list[str], mn: tuple[int, int]) -> str | None:
    cands = [v for v in versions if minor(v) == mn]
    return max(cands, key=parse_version) if cands else None


def cluster_steps(cluster: dict, target: str, channel_versions: dict, max_skew: int) -> tuple[list[dict], list[str]]:
    """Ordered steps for one cluster, plus blocker reasons found while building them."""
    reasons: list[str] = []
    avail = channel_versions.get(cluster["channel"], [])
    if target not in avail:
        return [], [f"target {target} is not available in the {cluster['channel']} channel"]
    cp = cluster["control_plane"]
    if parse_version(cp) > parse_version(target):
        return [], [f"control plane {cp} is newer than the target {target}"]
    pools = {p["name"]: p["version"] for p in cluster["node_pools"]}
    steps: list[dict] = []
    cur = minor(cp)
    tmin = minor(target)
    # one minor at a time for the control plane
    hops: list[str] = []
    for m in range(cur[1] + 1, tmin[1]):
        v = best_in_minor(avail, (tmin[0], m))
        if v is None:
            return [], [f"no {tmin[0]}.{m} version in the {cluster['channel']} channel for the intermediate hop"]
        hops.append(v)
    hops.append(target)
    for hop in hops:
        # before the control plane moves to `hop`, every pool must be within skew of it
        for name in sorted(pools):
            pv = pools[name]
            if minor(hop)[1] - minor(pv)[1] > max_skew:
                to = cp  # pools can never be newer than the control plane
                if minor(hop)[1] - minor(to)[1] > max_skew:
                    return [], [f"node pool {name} at {pv} cannot reach skew of {hop}"]
                if to != pv:
                    steps.append({"kind": "node_pool", "pool": name, "from": pv, "to": to,
                                  "minor": minor(to) != minor(pv), "reason": "skew"})
                    pools[name] = to
        if hop != cp:
            steps.append({"kind": "control_plane", "from": cp, "to": hop, "minor": minor(hop) != minor(cp)})
            cp = hop
    for name in sorted(pools):
        if pools[name] != target:
            steps.append({"kind": "node_pool", "pool": name, "from": pools[name], "to": target,
                          "minor": minor(target) != minor(pools[name])})
            pools[name] = target
    return steps, reasons


def static_blockers(cluster: dict) -> list[str]:
    out = []
    for pdb in cluster.get("pdbs", []):
        if pdb.get("disruptions_allowed", 1) <= 0:
            out.append(f"PDB {pdb['namespace']}/{pdb['name']} allows 0 disruptions: node drains would stall")
    q = cluster.get("quota", {})
    need = 0
    for p in cluster["node_pools"]:
        s = p.get("strategy", {})
        if s.get("type") == "BLUE_GREEN":
            need = max(need, p["node_count"] * p["vcpus_per_node"])
        else:
            need = max(need, s.get("max_surge", 1) * p["vcpus_per_node"])
    if q and q["cpus_used"] + need > q["cpus_limit"]:
        out.append(f"CPU quota: upgrade needs {need} extra vCPUs, {q['cpus_limit'] - q['cpus_used']} free")
    return out


def window_ok(start: dt.datetime, end: dt.datetime, steps: list[dict], exclusions: list[dict]) -> bool:
    for ex in exclusions:
        es, ee = ts(ex["start"]), ts(ex["end"])
        if start >= ee or end <= es:
            continue
        for s in steps:
            if ex["scope"] in BLOCKING_SCOPES[(s["kind"], s["minor"])]:
                return False
    return True


def plan(fleet: dict) -> dict:
    target = fleet["target_version"]
    policy = fleet["policy"]
    now = ts(fleet["now"])
    order = policy["environment_order"]
    clusters = sorted(fleet["clusters"], key=lambda c: (order.index(c["environment"]), not c.get("canary", False), c["name"]))
    waves: list[dict] = []
    blocked: list[dict] = []
    held: list[str] = []
    earliest = now
    last_start: dt.datetime | None = None
    halted = False
    for env in order:
        wave = {"environment": env, "clusters": []}
        wave_clusters = [c for c in clusters if c["environment"] == env]
        for c in wave_clusters:
            if halted:
                held.append(c["name"])
                continue
            steps, reasons = cluster_steps(c, target, fleet["channel_versions"], policy["max_node_skew"])
            reasons += static_blockers(c) if steps else []
            if reasons:
                blocked.append({"cluster": c["name"], "reasons": reasons})
                halted = True
                continue
            if not steps:
                continue  # already at target
            for start, end in window_occurrences(c["maintenance_window"], earliest):
                if window_ok(start, end, steps, c.get("exclusions", [])):
                    break
            else:
                blocked.append({"cluster": c["name"], "reasons": [f"no allowed maintenance window in {HORIZON_DAYS} days"]})
                halted = True
                continue
            wave["clusters"].append({"cluster": c["name"], "window_start": iso(start), "steps": steps})
            last_start = start
            earliest = start + dt.timedelta(hours=policy["cluster_gap_hours"])
        if wave["clusters"]:
            waves.append(wave)
            earliest = max(earliest, last_start + dt.timedelta(hours=policy["soak_hours"][env]))
    return {"target_version": target, "waves": waves, "blocked": blocked, "held": held}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("fleet")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        fleet = json.loads(Path(args.fleet).read_text())
        if not isinstance(fleet, dict):
            raise ValueError("fleet file must be a JSON object")
        result = plan(fleet)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"planner: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Upgrade plan to {result['target_version']}")
        for w in result["waves"]:
            print(f"wave {w['environment']}:")
            for c in w["clusters"]:
                print(f"  {c['cluster']} window {c['window_start']}")
                for s in c["steps"]:
                    what = "control plane" if s["kind"] == "control_plane" else f"pool {s['pool']}"
                    print(f"    {what}: {s['from']} -> {s['to']}")
        for b in result["blocked"]:
            print(f"BLOCKED {b['cluster']}: " + "; ".join(b["reasons"]))
        if result["held"]:
            print("held (after a blocked cluster): " + ", ".join(result["held"]))
    return 1 if result["blocked"] else 0


if __name__ == "__main__":
    sys.exit(main())
