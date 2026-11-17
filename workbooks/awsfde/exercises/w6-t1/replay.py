"""Replay the morning's page loads through CloudFront -> Lambda -> Quick Sight and write run/ (done).

Each page load: the SPA's index and bundle (static), then GET /api/analytics/embed-url with the
user's token, then the Embedding SDK redeems the URL after the browser's redeem delay.
Usage: python replay.py [outdir]
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import logging
import pathlib
import sys

from api.embed_handler import handler
from edge.cloudfront import Distribution
from edge.quicksight import FakeQuickSight

ROOT = pathlib.Path(__file__).resolve().parent
DAY = dt.datetime(2026, 11, 12, tzinfo=dt.timezone.utc)


def ts(t: float) -> str:
    return (DAY + dt.timedelta(seconds=t)).strftime("%Y-%m-%d\t%H:%M:%S")


def run(out: str = "run") -> dict:
    outdir = pathlib.Path(out) if pathlib.Path(out).is_absolute() else ROOT / out
    outdir.mkdir(exist_ok=True)
    dist = Distribution(ROOT / "config" / "distribution.json")
    qs = FakeQuickSight()
    lam_log = (outdir / "lambda.log").open("w")
    handler_log = logging.getLogger("tidewater.embed")
    handler_log.handlers[:] = [logging.StreamHandler(lam_log)]
    handler_log.setLevel(logging.INFO)
    handler_log.propagate = False
    cf_lines = ["#Version: 1.0", "#Fields: date time x-edge-location sc-status cs-method cs-uri-stem cs-uri-query "
                "x-edge-result-type time-taken cs(Cache-Control)-resp tenant(token)"]
    pending = []
    loads = list(csv.DictReader((ROOT / "evidence" / "page-loads.csv").open()))
    origin_calls = {"n": 0}
    for i, row in enumerate(loads, start=1):
        now = float(row["t_seconds"])
        tenant, user = row["tenant_id"], row["username"]
        token = {"tenant_id": tenant, "username": user}
        for asset in ("/index.html", "/assets/app.js"):
            resp, kind, _ = dist.get(now, asset, "", {}, lambda p, q, h: {"statusCode": 200, "headers": {"cache-control": "max-age=3600"}, "body": ""})
            cf_lines.append(f"{ts(now)}\tIAD89-P1\t200\tGET\t{asset}\t-\t{kind}\t0.002\tmax-age=3600\t-")

        def origin(path, query, headers, _tok=token, _now=now):
            origin_calls["n"] += 1
            qs.clock = _now
            ev = {"version": "2.0", "routeKey": "GET /api/analytics/embed-url",
                  "requestContext": {"authorizer": {"jwt": {"claims": headers["x-verified-claims"]}}}}
            lam_log.write(f"{ts(_now)} START tenant={_tok['tenant_id']} user={_tok['username']}\n")
            return handler(ev, qs)

        resp, kind, _ = dist.get(now, "/api/analytics/embed-url", "dashboard=dash-ops",
                                 {"authorization": f"Bearer <jwt for {user}>", "x-verified-claims": token}, origin)
        cc = {k.lower(): v for k, v in resp.get("headers", {}).items()}.get("cache-control", "-")
        cf_lines.append(f"{ts(now)}\tIAD89-P1\t{resp['statusCode']}\tGET\t/api/analytics/embed-url\tdashboard=dash-ops\t"
                        f"{kind}\t{0.004 if kind == 'Hit' else 0.180}\t{cc}\t{tenant}")
        if resp["statusCode"] == 200:
            url = json.loads(resp["body"])["embedUrl"]
            pending.append((now + int(row["redeem_delay_ms"]) / 1000.0, url, tenant, f"load-{i:03d}"))
    for when, url, tenant, load_id in sorted(pending):
        qs.redeem(when, url, tenant, load_id)
    lam_log.close()
    (outdir / "cloudfront-access.log").write_text("\n".join(cf_lines) + "\n")
    (outdir / "quicksight-embed.log").write_text("".join(json.dumps(r) + "\n" for r in qs.redeems))
    api_lines = [l for l in cf_lines if "/api/" in l]
    bad = [r for r in qs.redeems if r["result"] != "ok"]
    cross = [r for r in qs.redeems if r["result"] == "ok" and r["data_tenant"] != r["viewer_tenant"]]
    summary = {
        "page_loads": len(loads), "embed_url_requests": len(api_lines), "blank_dashboards": len(bad),
        "blank_by_reason": {k: sum(1 for r in bad if r["result"] == k) for k in sorted({r["result"] for r in bad})},
        "views_of_another_tenants_data": len(cross),
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


if __name__ == "__main__":
    print(json.dumps(run(*sys.argv[1:]), indent=1))
