#!/usr/bin/env python3
"""Seeded generator for the w5-t1 TSDB fixtures (what Managed Service for Prometheus scraped).

  python tools/gen_tsdb.py incident  incident/tsdb-2026-11-04.json
Scenarios: incident, healthy, spike, slowburn, fastburn16, twoclusters, drift.
Counters are http_requests_total per pod and code, scraped every 30 s, with the labels managed
collection attaches through PodMonitoring: project_id, location, cluster, namespace, job, instance, pod.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import random
import sys

SCRAPE = 30


def ts(s: str) -> float:
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc).timestamp()


SCENARIOS = {
    # start, hours, clusters [(name, location, share)], outages [(cluster, start, minutes, error_ratio)]
    "incident": ("2026-11-04T06:00:00Z", 9, [("prod-blue", "us-central1", 1.0)], [("prod-blue", "2026-11-04T13:12:00Z", 38, 0.06)]),
    "healthy": ("2026-11-02T06:00:00Z", 9, [("prod-blue", "us-central1", 1.0)], []),
    "spike": ("2026-11-02T06:00:00Z", 9, [("prod-blue", "us-central1", 1.0)], [("prod-blue", "2026-11-02T13:00:00Z", 4, 0.20)]),
    "slowburn": ("2026-11-06T00:00:00Z", 12, [("prod-blue", "us-central1", 1.0)], [("prod-blue", "2026-11-06T06:30:00Z", 300, 0.012)]),
    "fastburn16": ("2026-11-06T00:00:00Z", 9, [("prod-blue", "us-central1", 1.0)], [("prod-blue", "2026-11-06T06:30:00Z", 90, 0.016)]),
    "twoclusters": ("2026-11-08T06:00:00Z", 9, [("prod-blue", "us-central1", 0.5), ("prod-green", "us-east4", 0.5)],
                    [("prod-green", "2026-11-08T13:00:00Z", 45, 0.06)]),
    "drift": ("2026-11-02T06:00:00Z", 9, [("prod-blue", "us-central1", 1.0)], []),
}
BASE_ERR = 0.0004
RPS = 120.0  # riq-api total requests per second per cluster at share 1.0


def gen(name: str) -> dict:
    start_s, hours, clusters, outages = SCENARIOS[name]
    rnd = random.Random(f"w5-t1:{name}")
    start = ts(start_s)
    end = start + hours * 3600
    outs = [(c, ts(s), ts(s) + m * 60, r) for c, s, m, r in outages]
    series = []

    def emit(labels, rate_fn):
        val, samples, t = rnd.randint(1000, 90000) * 1.0, [], start
        while t <= end:
            samples.append([t, round(val, 1)])
            val += max(0.0, rnd.gauss(rate_fn(t) * SCRAPE, (rate_fn(t) * SCRAPE) ** 0.5 + 0.01))
            t += SCRAPE
        series.append({"labels": labels, "samples": samples})

    job = "riq/riq-api" if name == "drift" else "riq-api"
    for cname, loc, share in clusters:
        pods = 3
        for p in range(pods):
            pod = f"riq-api-7c9d{p}f6b5-{'xkqzv'[p:p + 3] or 'abc'}{p}"
            base = {"__name__": "http_requests_total", "project_id": "tsl-riq-prod", "location": loc, "cluster": cname,
                    "namespace": "riq", "job": job, "instance": f"10.{8 + clusters.index((cname, loc, share))}.1.{12 + p}:8080", "pod": pod}

            def err_ratio(t, cname=cname):
                for c, a, b, r in outs:
                    if c == cname and a <= t < b:
                        return r
                return BASE_ERR
            per_pod = RPS * share / pods
            emit({**base, "code": "200"}, lambda t, f=err_ratio: per_pod * (1 - f(t)) * 0.97)
            emit({**base, "code": "404"}, lambda t, f=err_ratio: per_pod * (1 - f(t)) * 0.03)
            emit({**base, "code": "503"}, lambda t, f=err_ratio: per_pod * f(t))
    # A neighbour with its own error rate: must never page RIQ.
    for p in range(2):
        base = {"__name__": "http_requests_total", "project_id": "tsl-mdm-prod", "location": "us-central1", "cluster": "prod-blue",
                "namespace": "mdm", "job": "mdm-api", "instance": f"10.8.2.{20 + p}:8080", "pod": f"mdm-api-5f7b8-{p}q"}
        emit({**base, "code": "200"}, lambda t: 30.0 * 0.9)
        emit({**base, "code": "500"}, lambda t: 30.0 * 0.1)
    return {"scenario": name, "scrape_interval_s": SCRAPE, "series": series}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 2 or argv[0] not in SCENARIOS:
        print(f"usage: gen_tsdb.py <{'|'.join(SCENARIOS)}> <out.json>", file=sys.stderr)
        return 2
    out = pathlib.Path(argv[1])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(gen(argv[0]), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
