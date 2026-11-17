#!/usr/bin/env python3
"""Generate the incident bundle for backend/w3-t1 into <out>/ (deterministic, stdlib + contacts_api.seed)."""

from __future__ import annotations

import base64
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from contacts_api.seed import IMPORT_TS, make_rows  # noqa: E402

TENANT = "app-partner-portal"
ORGANIC, BULK, LIMIT = 1931, 500, 100


def replay_partner_walk(rows):
    """What the partner sync saw on 2026-11-12 (the production query at the time)."""
    ordered = sorted(rows, key=lambda r: r["created_at"])  # ties come back in heap order
    pages, after = [], None
    while True:
        cand = [r for r in ordered if after is None or r["created_at"] > after]
        page = cand[:LIMIT]
        pages.append((after, page))
        if len(page) < LIMIT:
            return pages
        after = page[-1]["created_at"]


def main(out: str) -> None:
    o = pathlib.Path(out)
    o.mkdir(parents=True, exist_ok=True)
    rows = make_rows(TENANT, ORGANIC, BULK)
    pages = replay_partner_walk(rows)
    synced = sum(len(p) for _, p in pages)
    missing = len(rows) - synced
    rng = random.Random(7)

    log, access = [], []
    t = 0
    for n, (after, page) in enumerate(pages, 1):
        cur = "" if after is None else "&cursor=" + base64.urlsafe_b64encode(after.encode()).decode()
        hhmm = lambda s: "2026-11-12T09:%02d:%02dZ" % (s // 60, s % 60)  # noqa: E731
        if n in (7, 8, 19):
            log.append(f"{hhmm(t)} WARN  GET /v1/contacts?limit={LIMIT}{cur} -> 429 Too Many Requests retry-after=2")
            t += 2
        log.append(f"{hhmm(t)} INFO  GET /v1/contacts?limit={LIMIT}{cur} -> 200 rows={len(page)}")
        access.append({"ts": hhmm(t), "route": "/v1/contacts", "tenant": TENANT, "limit": LIMIT,
                       "cursor_after": after, "rows": len(page),
                       "last_created_at": page[-1]["created_at"] if page else None,
                       "latency_ms": rng.randint(9, 40), "status": 200})
        t += 1
    log.append(f"2026-11-12T09:{t // 60:02d}:{t % 60:02d}Z INFO  sync complete pages={len(pages)} contacts_received={synced}")
    log.append(f"2026-11-12T09:{t // 60:02d}:{t % 60:02d}Z WARN  reconcile: source reports total={len(rows)} received={synced} missing={missing}")
    (o / "partner-sync.log").write_text("\n".join(log) + "\n")
    (o / "accounts-svc-access.jsonl").write_text("\n".join(json.dumps(a) for a in access) + "\n")

    by_day = {}
    for r in rows:
        by_day[r["created_at"][:10]] = by_day.get(r["created_at"][:10], 0) + 1
    ties = {}
    for r in rows:
        ties[r["created_at"]] = ties.get(r["created_at"], 0) + 1
    top = sorted(ties.items(), key=lambda kv: -kv[1])[:3]
    lines = ["-- psql on the accounts-svc replica, 2026-11-12 10:05", f"-- tenant {TENANT}", "",
             "SELECT count(*) FROM contacts WHERE tenant_id = 'app-partner-portal';", f" count = {len(rows)}", "",
             "SELECT created_at::date AS day, count(*) FROM contacts WHERE tenant_id = 'app-partner-portal' GROUP BY 1 ORDER BY 1;"]
    lines += [f" {d} | {c}" for d, c in sorted(by_day.items())]
    lines += ["", "SELECT created_at, count(*) FROM contacts WHERE tenant_id = 'app-partner-portal'",
              "GROUP BY 1 ORDER BY 2 DESC LIMIT 3;"]
    lines += [f" {k} | {v}" for k, v in top]
    (o / "replica-queries.txt").write_text("\n".join(lines) + "\n")

    (o / "TICKET.md").write_text(f"""# KEY-2291: Partner contact sync missing contacts since the November import

**Reporter:** Marketing Ops (partner portal integration), 2026-11-12 10:02
**Severity:** S2 (campaign launch on 2026-11-16 uses this audience)

Our nightly full sync from `GET /v1/contacts` (tenant `{TENANT}`) received {synced} contacts, but your
count endpoint and the partner portal both say {len(rows)}. That is {missing} contacts missing from our side.
The sync code has not changed in 4 months and it worked until last week.

We did notice your API rate limiting us during the run (a few 429s, see the attached log). Our client
honors Retry-After and retries, but maybe the retried pages lost data? Could you raise our limit?

Attached: `partner-sync.log`. On-call (Marcus Oyelaran) added `accounts-svc-access.jsonl` (decoded
cursors) and `replica-queries.txt`.

Context from the accounts team: the partner portal contacts were bulk-loaded on 2026-11-02 with one
INSERT ... SELECT during the migration rehearsal.
""")
    print(f"bundle written to {o}: total={len(rows)} synced={synced} missing={missing}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "incident")
