#!/usr/bin/env python3
"""Offline rule runner for platform/w5-t1: evaluates a Prometheus rule file over a TSDB fixture.

  python tools/eval_rules.py --rules rules/riq-slo.rules.yaml --tsdb incident/tsdb-2026-11-04.json
  python tools/eval_rules.py --tsdb incident/tsdb-2026-11-04.json --query 'sum by (job) (rate(http_requests_total[5m]))' --at 2026-11-04T13:30:00Z

Every group is evaluated every --step seconds (default 60) from the first sample to the last, rules in
file order; recording rule results are written back to the TSDB so later rules (and later steps) can
select them. Alerts honour `for:`. Output: one line per alert that fired (or JSON with --json).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import promql_mini as pm  # noqa: E402


def iso(t: float) -> str:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(s: str) -> float:
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp()


def parse_for(s) -> float:
    if not s:
        return 0.0
    total = 0.0
    for n, u in re.findall(r"(\d+)([smhd])", str(s)):
        total += int(n) * pm.DUR[u]
    return total


def load_rules(path: str) -> list[dict]:
    doc = yaml.safe_load(pathlib.Path(path).read_text()) or {}
    groups = doc.get("groups") or []
    out = []
    for g in groups:
        rules = []
        for r in g.get("rules") or []:
            if "record" not in r and "alert" not in r:
                raise ValueError(f"rule without record/alert in group {g.get('name')}")
            rules.append({**r, "_ast": pm.parse(str(r["expr"]))})
        out.append({"name": g.get("name"), "rules": rules})
    return out


def run(groups: list[dict], db: pm.TSDB, start: float, end: float, step: float = 60.0) -> list[dict]:
    """Evaluate all groups from start to end. Returns alert events (first firing per label set)."""
    pending: dict[tuple, float] = {}
    events: dict[tuple, dict] = {}
    t = start
    while t <= end:
        for g in groups:
            for r in g["rules"]:
                res = pm.evaluate(r["_ast"], db, t)
                if not isinstance(res, list):
                    res = [({}, res)]
                if "record" in r:
                    for labels, v in res:
                        out = {**pm.strip_name(labels), **(r.get("labels") or {}), "__name__": r["record"]}
                        db.add(out, t, v)
                    continue
                active = set()
                for labels, _ in res:
                    al = {**pm.strip_name(labels), **(r.get("labels") or {}), "alertname": r["alert"]}
                    k = tuple(sorted(al.items()))
                    active.add(k)
                    pending.setdefault(k, t)
                    if t - pending[k] >= parse_for(r.get("for")) and k not in events:
                        events[k] = {"alert": r["alert"], "labels": al, "active_at": pending[k], "fired_at": t}
                for k in [k for k in pending if dict(k)["alertname"] == r["alert"] and k not in active]:
                    del pending[k]
        t += step
    return sorted(events.values(), key=lambda e: (e["fired_at"], e["alert"]))


def time_range(db: pm.TSDB) -> tuple[float, float]:
    ts = [s.ts for s in db.series.values() if s.ts]
    return min(x[0] for x in ts), max(x[-1] for x in ts)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules")
    ap.add_argument("--tsdb", required=True)
    ap.add_argument("--step", type=float, default=60.0)
    ap.add_argument("--from", dest="frm")
    ap.add_argument("--to")
    ap.add_argument("--query")
    ap.add_argument("--at")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    db = pm.TSDB.from_json(json.loads(pathlib.Path(a.tsdb).read_text()))
    lo, hi = time_range(db)
    if a.query:
        t = parse_time(a.at) if a.at else hi
        res = pm.query(a.query, db, t)
        if isinstance(res, list):
            for labels, v in sorted(res, key=lambda x: sorted(x[0].items())):
                print(f"{json.dumps(labels, sort_keys=True)} {v:.6g}")
            if not res:
                print("(empty vector)")
        else:
            print(f"scalar {res:.6g}")
        return 0
    if not a.rules:
        ap.error("--rules or --query is required")
    groups = load_rules(a.rules)
    start = parse_time(a.frm) if a.frm else lo
    end = parse_time(a.to) if a.to else hi
    events = run(groups, db, start, end, a.step)
    if a.json:
        print(json.dumps([{**e, "active_at": iso(e["active_at"]), "fired_at": iso(e["fired_at"])} for e in events], indent=2))
    else:
        print(f"evaluated {len(groups)} group(s) from {iso(start)} to {iso(end)} every {a.step:g}s")
        for e in events:
            extra = {k: v for k, v in e["labels"].items() if k != "alertname"}
            print(f"FIRING {e['alert']} active {iso(e['active_at'])} fired {iso(e['fired_at'])} {json.dumps(extra, sort_keys=True)}")
        if not events:
            print("no alerts fired")
    return 0


if __name__ == "__main__":
    sys.exit(main())
