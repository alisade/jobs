// Hidden tests for backend/w2-t1 (run from tests/__hidden__/).
import * as fs from "fs";
import * as path from "path";
import type { PGlite } from "@electric-sql/pglite";
import { timelinePage, nextCursor, TimelineRow } from "../../src/timelineRepo";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { ROOT, openSeeded, orbitalId, kdbQuery, loadQuery } = require("../../scripts/db.js");

const REF = `SELECT id, type, subject, occurred_at FROM activities
  WHERE tenant_id = $1 AND account_id = $2::uuid AND (occurred_at, id) < ($3::timestamptz, $4::bigint)
  ORDER BY occurred_at DESC, id DESC LIMIT 50`;

let db: PGlite;
let acct: string;
let plan = "";
beforeAll(async () => {
  db = await openSeeded();
  acct = await orbitalId(db);
  const sql = loadQuery(path.join(ROOT, "queries", "timeline.sql"));
  const r = await kdbQuery(db, sql, ["bu-emea", acct, "infinity", "9223372036854775807"], "EXPLAIN (ANALYZE, BUFFERS) ");
  plan = r.rows.map((x: Record<string, string>) => x["QUERY PLAN"]).join("\n");
});
afterAll(async () => { if (db) await db.close(); });

test("the plan seeks the timeline index on account_id (Index Cond, not a Filter)", () => {
  expect(plan).toMatch(/Index Cond: [^\n]*account_id = /);
  expect(plan).not.toMatch(/Filter: [^\n]*account_id/);
});

test("no Seq Scan and no Sort: the index delivers rows in timeline order", () => {
  expect(plan).not.toMatch(/Seq Scan on activities/);
  expect(plan).not.toMatch(/->\s+Sort|^Sort/m);
});

test("first page touches a handful of buffers, not thousands", () => {
  const m = plan.match(/Buffers: shared hit=(\d+)/);
  expect(m).not.toBeNull();
  expect(Number(m![1])).toBeLessThan(100);
});

test("three pages match the reference query row for row", async () => {
  let cur = undefined as undefined | { occurredAt: string; id: string };
  let refCur = { occurredAt: "infinity", id: "9223372036854775807" };
  for (let page = 0; page < 3; page++) {
    const got: TimelineRow[] = await timelinePage(db, "bu-emea", acct, cur);
    const want = (await db.query<TimelineRow>(REF, ["bu-emea", acct, refCur.occurredAt, refCur.id])).rows;
    expect(got.map((r) => Number(r.id))).toEqual(want.map((r) => Number(r.id)));
    cur = nextCursor(got)!;
    refCur = cur;
  }
});

test("another tenant gets nothing for Orbital Freight's account id", async () => {
  expect(await timelinePage(db, "bu-amer", acct)).toHaveLength(0);
});

test("ANSWER.md names the column cast as the root cause and the index it defeated", () => {
  const text = fs.readFileSync(path.join(ROOT, "ANSWER.md"), "utf8").replace(/<!--[\s\S]*?-->/g, "");
  expect(text).toMatch(/::text|\bcast/i);
  expect(text).toMatch(/index/i);
});
