// make explain: EXPLAIN (ANALYZE, BUFFERS) of queries/timeline.sql for Orbital Freight, first page,
// called the way pipeline-svc calls it (kdb, string params declared as text).
"use strict";
const path = require("path");
const { ROOT, openSeeded, kdbQuery, loadQuery, orbitalId } = require("./db.js");
(async () => {
  const file = process.argv[2] || path.join(ROOT, "queries", "timeline.sql");
  const db = await openSeeded();
  const acct = await orbitalId(db);
  const r = await kdbQuery(db, loadQuery(file), ["bu-emea", acct, "infinity", "9223372036854775807"], "EXPLAIN (ANALYZE, BUFFERS) ");
  console.log(`-- ${path.relative(ROOT, file)} (account ${acct}, tenant bu-emea)`);
  console.log(r.rows.map((x) => x["QUERY PLAN"]).join("\n"));
  await db.close();
})().catch((e) => { console.error("explain failed: " + e.message); process.exit(1); });
