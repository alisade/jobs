// Print EXPLAIN (ANALYZE, BUFFERS) for queries/*.sql against freshly migrated and seeded data,
// running as keystone_app with app.tenant_id = bu-emea (what a service request looks like).
"use strict";
const fs = require("fs");
const path = require("path");
const { openDb, applyDir } = require("bk-kit");
const root = path.resolve(__dirname, "..");
const harness = fs.readFileSync(path.join(root, "tests", "harness.ts"), "utf8");
const SEED = harness.split("export const SEED = `")[1].split("`;")[0];
const PARAMS = {
  "timeline.sql": (acct) => [acct, "2026-11-02T00:00:00Z", 9999999],
  "my_open_opportunities.sql": () => ["u7"],
  "custom_field_search.sql": () => ['{"region_code": "R17"}'],
};
(async () => {
  const db = await openDb();
  await applyDir(db, path.join(root, "migrations"));
  await db.exec(SEED);
  const acct = (await db.query("SELECT id FROM accounts WHERE tenant_id = 'bu-emea' LIMIT 1")).rows[0].id;
  for (const f of Object.keys(PARAMS)) {
    const sql = fs.readFileSync(path.join(root, "queries", f), "utf8").replace(/;\s*$/, "");
    await db.exec("BEGIN; SET LOCAL ROLE keystone_app;");
    await db.query("SELECT set_config('app.tenant_id', 'bu-emea', true)");
    const r = await db.query(`EXPLAIN (ANALYZE, BUFFERS) ${sql}`, PARAMS[f](acct));
    await db.exec("ROLLBACK;");
    console.log(`== ${f}`);
    console.log(r.rows.map((x) => x["QUERY PLAN"]).join("\n") + "\n");
  }
  await db.close();
})().catch((e) => { console.error(e.message); process.exit(1); });
