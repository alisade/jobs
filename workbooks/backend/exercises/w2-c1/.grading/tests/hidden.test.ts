// Hidden tests for backend/w2-c1 (copied to tests/__hidden__/ by the grader).
import type { PGlite } from "@electric-sql/pglite";
import { freshDb, asApp, count, rejects, appRejects, plan, query } from "../harness";

let db: PGlite;
beforeAll(async () => { db = await freshDb(); });
afterAll(async () => { if (db) await db.close(); });

const TABLES = ["accounts", "contacts", "opportunities", "activities"];

test("no tenant set: every tenant table returns zero rows for keystone_app", async () => {
  for (const t of TABLES) {
    expect([t, await asApp(db, null, () => count(db, `SELECT 1 FROM ${t}`))]).toEqual([t, 0]);
  }
});

test("each tenant sees exactly its own rows in every table", async () => {
  for (const t of TABLES) {
    const total = await count(db, `SELECT 1 FROM ${t} WHERE tenant_id = 'bu-apac'`);
    const seen = await asApp(db, "bu-apac", () => count(db, `SELECT 1 FROM ${t}`));
    expect([t, seen]).toEqual([t, total]);
  }
});

test("RLS is FORCEd on every tenant table and keystone_app cannot bypass it or log in", async () => {
  const r = await db.query<{ relname: string; relrowsecurity: boolean; relforcerowsecurity: boolean }>(
    "SELECT relname, relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = ANY($1) ORDER BY relname", [TABLES]);
  expect(r.rows.length).toBe(4);
  for (const row of r.rows) expect([row.relname, row.relrowsecurity, row.relforcerowsecurity]).toEqual([row.relname, true, true]);
  const role = await db.query<{ rolbypassrls: boolean; rolcanlogin: boolean; rolsuper: boolean }>(
    "SELECT rolbypassrls, rolcanlogin, rolsuper FROM pg_roles WHERE rolname = 'keystone_app'");
  expect(role.rows).toEqual([{ rolbypassrls: false, rolcanlogin: false, rolsuper: false }]);
});

test("keystone_app can write rows for its own tenant (grants are in place)", async () => {
  const msg = await appRejects(db, "bu-emea",
    "INSERT INTO activities (tenant_id, account_id, type, subject, occurred_at) " +
    "SELECT tenant_id, id, 'call', 'Intro call', now() FROM accounts LIMIT 1");
  expect(msg).toBe("");
});

test("inserting a row for another tenant is rejected by the policy (WITH CHECK)", async () => {
  const acct = (await db.query<{ id: number }>("SELECT id FROM accounts WHERE tenant_id = 'bu-amer' LIMIT 1")).rows[0].id;
  const msg = await appRejects(db, "bu-emea",
    "INSERT INTO activities (tenant_id, account_id, type, subject, occurred_at) VALUES ('bu-amer', $1, 'call', 'x', now())", [acct]);
  expect(msg).toMatch(/row-level security|policy/i);
});

test("an update cannot move a row into another tenant", async () => {
  const msg = await appRejects(db, "bu-emea", "UPDATE accounts SET tenant_id = 'bu-amer' WHERE id IN (SELECT id FROM accounts LIMIT 1)");
  expect(msg).toMatch(/row-level security|policy|violates/i);
});

test("a child row cannot reference a parent in another tenant, even as the owner (composite FK)", async () => {
  const amer = (await db.query<{ id: number }>("SELECT id FROM accounts WHERE tenant_id = 'bu-amer' LIMIT 1")).rows[0].id;
  for (const sql of [
    "INSERT INTO contacts (tenant_id, account_id, first_name, last_name, email) VALUES ('bu-emea', $1, 'A', 'B', 'cross@example.test')",
    "INSERT INTO opportunities (tenant_id, account_id, owner_id, name, stage, amount) VALUES ('bu-emea', $1, 'u1', 'X', 'prospecting', 1)",
    "INSERT INTO activities (tenant_id, account_id, type, subject, occurred_at) VALUES ('bu-emea', $1, 'call', 'x', now())",
  ]) {
    expect(await rejects(db, sql, [amer])).toMatch(/foreign key/i);
  }
  const contact = (await db.query<{ id: number }>("SELECT id FROM contacts WHERE tenant_id = 'bu-amer' LIMIT 1")).rows[0].id;
  const emeaAcct = (await db.query<{ id: number }>("SELECT id FROM accounts WHERE tenant_id = 'bu-emea' LIMIT 1")).rows[0].id;
  expect(await rejects(db,
    "INSERT INTO activities (tenant_id, account_id, contact_id, type, subject, occurred_at) VALUES ('bu-emea', $1, $2, 'call', 'x', now())",
    [emeaAcct, contact])).toMatch(/foreign key/i);
});

test("a soft-deleted contact's email can be reused", async () => {
  await db.exec("BEGIN;");
  try {
    await db.query("UPDATE contacts SET deleted_at = now() WHERE id = 2");
    await db.query("INSERT INTO contacts (tenant_id, account_id, first_name, last_name, email) " +
      "SELECT tenant_id, account_id, 'New', 'Owner', email FROM contacts WHERE id = 2");
  } finally {
    await db.exec("ROLLBACK;");
  }
});

test("closed stages need a close_date and amounts cannot be negative", async () => {
  const base = "INSERT INTO opportunities (tenant_id, account_id, owner_id, name, stage, amount, close_date) SELECT tenant_id, id, 'u1', 'X', ";
  expect(await rejects(db, base + "'closed_won', 100, NULL FROM accounts WHERE id = 1")).toMatch(/check constraint|violates/i);
  expect(await rejects(db, base + "'closed_lost', 100, NULL FROM accounts WHERE id = 1")).toMatch(/check constraint|violates/i);
  expect(await rejects(db, base + "'proposal', -5, NULL FROM accounts WHERE id = 1")).toMatch(/check constraint|violates/i);
  expect(await rejects(db, base + "'closed_won', 100, date '2026-10-01' FROM accounts WHERE id = 1")).toBe("");
});

test("legacy sf_id is unique per tenant but may repeat across tenants", async () => {
  const dupe = await rejects(db, "INSERT INTO accounts (tenant_id, name, owner_id, sf_id) VALUES ('bu-amer', 'A', 'u1', 'LEGACY0000000001AA'), ('bu-amer', 'B', 'u1', 'LEGACY0000000001AA')");
  expect(dupe).toMatch(/duplicate key|unique/i);
  const ok = await rejects(db, "INSERT INTO accounts (tenant_id, name, owner_id, sf_id) VALUES ('bu-amer', 'A', 'u1', 'LEGACY0000000002AA'), ('bu-emea', 'B', 'u1', 'LEGACY0000000002AA')");
  expect(ok).toBe("");
});

test("custom_fields has a GIN index", async () => {
  const r = await db.query<{ indexdef: string }>("SELECT indexdef FROM pg_indexes WHERE tablename = 'accounts'");
  expect(r.rows.some((x) => /USING gin/i.test(x.indexdef) && /custom_fields/.test(x.indexdef))).toBe(true);
});

async function appPlan(sql: string, params: unknown[]): Promise<string> {
  return asApp(db, "bu-emea", () => plan(db, sql, params));
}

test("account timeline uses an index, no Seq Scan on activities and no Sort of the whole account", async () => {
  const acct = (await db.query<{ id: number }>("SELECT id FROM accounts WHERE tenant_id = 'bu-emea' LIMIT 1")).rows[0].id;
  const p = await appPlan(query("timeline.sql"), [acct, "2026-11-02T00:00:00Z", 9999999]);
  expect(p).not.toMatch(/Seq Scan on activities/);
  expect(p).toMatch(/Index/);
});

test("my open opportunities uses an index, no Seq Scan on opportunities", async () => {
  const p = await appPlan(query("my_open_opportunities.sql"), ["u7"]);
  expect(p).not.toMatch(/Seq Scan on opportunities/);
  expect(p).toMatch(/Index/);
});

test("custom-field search does not Seq Scan accounts", async () => {
  const p = await appPlan(query("custom_field_search.sql"), ['{"region_code": "R17"}']);
  expect(p).not.toMatch(/Seq Scan on accounts/);
});
