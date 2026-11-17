// Visible tests for backend/w2-c1. The grader adds more (hidden) tests on the same requirements.
import type { PGlite } from "@electric-sql/pglite";
import { freshDb, asApp, count, rejects } from "./harness";

let db: PGlite;
beforeAll(async () => { db = await freshDb(); });
afterAll(async () => { if (db) await db.close(); });

test("migrations apply and the synthetic seed loads", async () => {
  expect(await count(db, "SELECT 1 FROM activities")).toBe(60000);
});

test("keystone_app without app.tenant_id sees zero accounts, not an error", async () => {
  const n = await asApp(db, null, () => count(db, "SELECT 1 FROM accounts"));
  expect(n).toBe(0);
});

test("keystone_app with a tenant set sees only that tenant's accounts", async () => {
  const rows = await asApp(db, "bu-emea", async () =>
    (await db.query<{ tenant_id: string }>("SELECT DISTINCT tenant_id FROM accounts")).rows);
  expect(rows.map((r) => r.tenant_id)).toEqual(["bu-emea"]);
});

test("an active contact email is unique per tenant, case-insensitively", async () => {
  const msg = await rejects(db,
    "INSERT INTO contacts (tenant_id, account_id, first_name, last_name, email) " +
    "SELECT tenant_id, account_id, 'Dup', 'Licate', upper(email) FROM contacts WHERE id = 1");
  expect(msg).toMatch(/duplicate key|unique/i);
});

test("an unknown opportunity stage is rejected by the database", async () => {
  const msg = await rejects(db,
    "INSERT INTO opportunities (tenant_id, account_id, owner_id, name, stage, amount) " +
    "SELECT tenant_id, id, 'u1', 'Bad', 'won_maybe', 10 FROM accounts WHERE id = 1");
  expect(msg).toMatch(/check constraint|violates/i);
});
