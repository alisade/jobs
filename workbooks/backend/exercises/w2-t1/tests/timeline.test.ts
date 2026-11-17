// Visible tests for backend/w2-t1: the timeline returns the right rows the way pipeline-svc calls it.
import type { PGlite } from "@electric-sql/pglite";
import { timelinePage, nextCursor } from "../src/timelineRepo";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { openSeeded, orbitalId } = require("../scripts/db.js");

let db: PGlite;
let acct: string;
beforeAll(async () => { db = await openSeeded(); acct = await orbitalId(db); });
afterAll(async () => { if (db) await db.close(); });

test("first page: 50 rows, newest first", async () => {
  const rows = await timelinePage(db, "bu-emea", acct);
  expect(rows).toHaveLength(50);
  for (let i = 1; i < rows.length; i++) {
    expect(new Date(rows[i - 1].occurred_at).getTime()).toBeGreaterThanOrEqual(new Date(rows[i].occurred_at).getTime());
  }
});

test("keyset paging continues without overlap", async () => {
  const p1 = await timelinePage(db, "bu-emea", acct);
  const p2 = await timelinePage(db, "bu-emea", acct, nextCursor(p1)!);
  const ids1 = new Set(p1.map((r) => r.id));
  expect(p2).toHaveLength(50);
  expect(p2.some((r) => ids1.has(r.id))).toBe(false);
});
