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
# TODO: which maintenance-exclusion scopes block which kind of step?
#   key (component, is_minor) with component "control_plane" or "node_pool";
#   value: the set of scopes among NO_UPGRADES, NO_MINOR_UPGRADES, NO_MINOR_OR_NODE_UPGRADES.
#   Read "Maintenance windows and exclusions" (week 2 materials) before filling this in.
BLOCKING_SCOPES: dict[tuple[str, bool], set[str]] = {}


def best_in_minor(versions: list[str], mn: tuple[int, int]) -> str | None:
    cands = [v for v in versions if minor(v) == mn]
    return max(cands, key=parse_version) if cands else None


def cluster_steps(cluster: dict, target: str, channel_versions: dict, max_skew: int) -> tuple[list[dict], list[str]]:
    """Ordered steps for one cluster, plus blocker reasons.

    A step is {"kind": "control_plane", "from", "to", "minor": bool}
            or {"kind": "node_pool", "pool", "from", "to", "minor": bool}.
    TODO: see README "Steps for one cluster".
    """
    return [], []


def static_blockers(cluster: dict) -> list[str]:
    """TODO: PDBs that allow zero disruptions, and CPU quota for the upgrade strategy (README)."""
    return []


def window_ok(start: dt.datetime, end: dt.datetime, steps: list[dict], exclusions: list[dict]) -> bool:
    """TODO: False if an exclusion overlapping [start, end) blocks any of the steps."""
    return True


def plan(fleet: dict) -> dict:
    """TODO: waves in policy.environment_order, canary first, windows, gaps, soak, blocked and held."""
    return {"target_version": fleet["target_version"], "waves": [], "blocked": [], "held": []}


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
