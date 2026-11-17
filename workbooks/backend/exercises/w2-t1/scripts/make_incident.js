// Generates the incident bundle in incident/ (make setup). Deterministic except the live EXPLAIN
// timings, which come from PGlite on your machine.
"use strict";
const fs = require("fs");
const path = require("path");
const { ROOT, openSeeded, kdbQuery, loadQuery, orbitalId } = require("./db.js");

const OUT = path.join(ROOT, "incident");
const w = (name, text) => fs.writeFileSync(path.join(OUT, name), text.replace(/^\n/, ""));

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const db = await openSeeded();
  const acct = await orbitalId(db);
  const params = ["bu-emea", acct, "infinity", "9223372036854775807"];
  for (const [label, file, note] of [
    ["2026.43", "timeline-2026.43.sql", "kdb 3.8: parameters sent untyped, the server infers their types"],
    ["2026.44", "timeline-2026.44.sql", "kdb 4.0: every string parameter declared as text"],
  ]) {
    const sql = "EXPLAIN (ANALYZE, BUFFERS) " + loadQuery(path.join(ROOT, "scripts", file));
    const r = label === "2026.43" ? await db.query(sql, params) : await kdbQuery(db, sql, params);
    w(`explain-${label}.txt`, `-- captured by replaying the timeline query for Orbital Freight (${acct}) on the staging copy\n` +
      `-- release ${label}, first page; ${note}\n` + r.rows.map((x) => x["QUERY PLAN"]).join("\n") + "\n");
  }
  await db.close();

  w("PAGER.txt", `
[FIRING] pipeline-svc-timeline-latency (sev2)
  service: pipeline-svc   route: GET /v1/accounts/:id/timeline   env: prod
  p95 latency 1.84 s over 15m (SLO: p95 < 300 ms)  error budget burn: 14.2x
  started: 2026-11-04T14:19:00Z

#sales-ops-help (forwarded by Dana Whitfield):
  "Opening Orbital Freight in the account view spins for 2-3 seconds, sometimes the agent
   assistant times out when it asks for the timeline. Smaller accounts are a bit slow too."
`);
  w("oncall-timeline.md", `
# On-call log, 2026-11-04 (Marcus Oyelaran)

- 14:05 release 2026.44 of pipeline-svc rolled out (canary 10% 13:40, full 14:05)
- 14:19 pager: timeline p95 1.8 s
- 14:26 DB CPU on keystone-pg-prod up from 22% to 61%; no lock waits; connections 38/200
- 14:40 rolled the HPA from 6 to 10 pods: no change (latency is in the DB call span, 1.7 s)
- 14:55 Priya: "the autovacuum log shows activities was analyzed this morning, maybe the stats are off?"
- 15:20 ran ANALYZE activities by hand. Plan looks the same, p95 unchanged
- 15:31 Tomas: the nightly import added 900k activities over the weekend; maybe we just need to partition?
- 15:45 handing over to you. Rollback is possible but 2026.44 also ships the KEY-2291 fix that
  sales ops has been waiting for, so we would rather fix forward.
`);
  w("p95.txt", `
pipeline-svc GET /v1/accounts/:id/timeline, p95 (ms), 5-minute buckets, 2026-11-04 UTC

13:30  |####                      182
13:40  |#####                     205   <- canary 2026.44 (10%)
13:50  |######                    246
14:00  |########                  331
14:05  |##########################1650  <- 2026.44 at 100%
14:10  |##########################1790
14:20  |##########################1840
14:40  |##########################1810  <- HPA 6 -> 10 pods
15:20  |##########################1835  <- manual ANALYZE activities
15:40  |##########################1822
`);
  w("release-2026.44.diff", `
commit 7c1e9a2  KEY-2291 timeline: fix "operator does not exist: uuid = text" from kdb typed params

kdb now declares string parameters as text (2026.44 upgrade of the db wrapper). The timeline query
started failing with 42883 operator does not exist: uuid = text. Comparing as text fixes it.

diff --git a/queries/timeline.sql b/queries/timeline.sql
--- a/queries/timeline.sql
+++ b/queries/timeline.sql
@@ -5,7 +5,7 @@
 SELECT id, type, subject, occurred_at
 FROM activities
 WHERE tenant_id = $1
-  AND account_id = $2
+  AND account_id::text = $2
   AND (occurred_at, id) < ($3::timestamptz, $4::bigint)
 ORDER BY occurred_at DESC, id DESC
 LIMIT 50

diff --git a/package.json b/package.json
-    "@lumenfold/kdb": "3.8.2",
+    "@lumenfold/kdb": "4.0.0",
`);
  w("pg_stat_statements.txt", `
-- SELECT calls, round(mean_exec_time::numeric,1) mean_ms, shared_blks_hit, shared_blks_read, left(query,80)
--   FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 4;   (reset 2026-11-04 12:00, captured 15:10)
 calls  | mean_ms | shared_blks_hit | shared_blks_read | query
--------+---------+-----------------+------------------+--------------------------------------------------------------------------------
  41877 |  1412.6 |      9871442210 |         18227310 | SELECT id, type, subject, occurred_at FROM activities WHERE tenant_id = $1 AND account_id::text = $2 AND (o
   6120 |     3.9 |         2231409 |              120 | SELECT id, type, subject, occurred_at FROM activities WHERE tenant_id = $1 AND account_id = $2 AND (occurre
  95510 |     0.4 |         1910220 |                0 | SELECT id, name, stage, amount, close_date FROM opportunities WHERE owner_id = $1 AND stage NOT IN ($2, $3)
  12007 |     1.1 |          420118 |               14 | UPDATE opportunities SET stage = $1, version = version + $2 WHERE id = $3 AND version = $4
`);
  w("postgres.log", `
2026-11-04 06:12:44.120 UTC [4410] LOG:  automatic vacuum of table "keystone.public.activities": index scans: 1
        pages: 0 removed, 412220 remain, 31877 scanned (7.73% of total)
        tuples: 81210 removed, 30441877 remain, 0 are dead but not yet removable
2026-11-04 06:13:02.901 UTC [4410] LOG:  automatic analyze of table "keystone.public.activities"
2026-11-04 14:21:07.553 UTC [9122] LOG:  duration: 1871.204 ms  execute <unnamed>: SELECT id, type, subject, occurred_at FROM activities WHERE tenant_id = $1 AND account_id::text = $2 AND (occurred_at, id) < ($3::timestamptz, $4::bigint) ORDER BY occurred_at DESC, id DESC LIMIT 50
2026-11-04 14:21:07.553 UTC [9122] DETAIL:  parameters: $1 = 'bu-emea', $2 = '5ba8660c-4549-ae4f-5c93-0f73a54815fb', $3 = 'infinity', $4 = '9223372036854775807'
2026-11-04 14:22:31.018 UTC [9140] LOG:  duration: 644.880 ms  execute <unnamed>: SELECT id, type, subject, occurred_at FROM activities WHERE tenant_id = $1 AND account_id::text = $2 AND (occurred_at, id) < ($3::timestamptz, $4::bigint) ORDER BY occurred_at DESC, id DESC LIMIT 50
2026-11-04 15:20:12.004 UTC [9301] LOG:  statement: ANALYZE activities;
2026-11-04 15:20:15.771 UTC [9301] LOG:  duration: 3767.112 ms
`);
  console.log(`incident bundle written to ${path.relative(process.cwd(), OUT) || OUT}/`);
})().catch((e) => { console.error("make_incident failed: " + e.message); process.exit(1); });
