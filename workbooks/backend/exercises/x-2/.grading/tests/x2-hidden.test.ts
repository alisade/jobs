import * as fs from "fs";
import * as path from "path";
import { openDb } from "bk-kit";

const ROOT = path.resolve(__dirname, "..", "..");
const MIG = path.join(ROOT, "migrations");
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { migrate } = require("../../scripts/migrate");
// eslint-disable-next-line @typescript-eslint/no-var-requires
const ref = require("./lint-ref"); // the linter as shipped, not the copy in scripts/

const files = () => fs.readdirSync(MIG).filter((f) => /^\d{4}_.+\.sql$/.test(f)).sort();
const text = (f: string) => fs.readFileSync(path.join(MIG, f), "utf8");

let db: any;
beforeAll(async () => {
  db = await openDb();
  await migrate(db, { seedSql: fs.readFileSync(path.join(ROOT, "scripts", "seed.sql"), "utf8") });
});
afterAll(async () => { await db.close(); });

test("reference linter: no errors and the FK is validated somewhere", () => {
  const res = ref.lintDir(MIG);
  expect(res.filter((r: any) => r.level === "error")).toEqual([]);
  expect(res.filter((r: any) => r.rule === "not-valid-never-validated")).toEqual([]);
});

test("baseline migration untouched", () => {
  expect(files()[0]).toBe("0001_baseline.sql");
  expect(text("0001_baseline.sql")).toMatch(/activities_timeline_idx/);
  expect(text("0001_baseline.sql")).not.toMatch(/activities_contact/);
});

test("the contact FK exists and is validated after all migrations", async () => {
  const r = await db.query(
    "SELECT convalidated, pg_get_constraintdef(oid) AS def FROM pg_constraint WHERE conrelid = 'activities'::regclass AND conname = 'activities_contact_fk'");
  expect(r.rows).toHaveLength(1);
  expect(r.rows[0].convalidated).toBe(true);
  expect(r.rows[0].def).toMatch(/FOREIGN KEY \(tenant_id, contact_id\) REFERENCES contacts\(tenant_id, id\)/);
  const col = await db.query("SELECT 1 FROM information_schema.columns WHERE table_name = 'activities' AND column_name = 'contact_role'");
  expect(col.rows).toHaveLength(1);
});

test("the contact index exists, is valid and leads with tenant_id, contact_id", async () => {
  const r = await db.query(
    "SELECT i.indisvalid, pg_get_indexdef(i.indexrelid) AS def FROM pg_index i WHERE i.indrelid = 'activities'::regclass AND pg_get_indexdef(i.indexrelid) ~ '\\(tenant_id, contact_id'");
  expect(r.rows.length).toBeGreaterThanOrEqual(1);
  expect(r.rows[0].indisvalid).toBe(true);
});

test("the FK rejects a cross-tenant contact for new rows", async () => {
  const c = await db.query("SELECT id, tenant_id, account_id FROM contacts WHERE tenant_id = 'bu-amer' LIMIT 1");
  const a = await db.query("SELECT id FROM accounts WHERE tenant_id = 'bu-emea' LIMIT 1");
  await expect(db.query(
    "INSERT INTO activities (tenant_id, account_id, contact_id, type, subject, occurred_at) VALUES ('bu-emea', $1, $2, 'call', 'x', now())",
    [a.rows[0].id, c.rows[0].id])).rejects.toThrow(/activities_contact_fk/);
});

test("the FK is added NOT VALID with a lock_timeout, the index CONCURRENTLY outside a transaction", () => {
  const later = files().filter((f) => Number(f.slice(0, 4)) >= 57);
  const addFk = later.find((f) => /ADD\s+CONSTRAINT\s+activities_contact_fk/i.test(text(f)));
  expect(addFk).toBeDefined();
  expect(text(addFk!)).toMatch(/NOT\s+VALID/i);
  expect(text(addFk!)).toMatch(/lock_timeout/i);
  const idx = later.find((f) => /CREATE\s+INDEX/i.test(text(f)));
  expect(idx).toBeDefined();
  expect(text(idx!)).toMatch(/CONCURRENTLY/i);
  expect(text(idx!)).toMatch(/^--\s*kmigrate:no-transaction/);
  const validate = later.find((f) => /VALIDATE\s+CONSTRAINT\s+activities_contact_fk/i.test(text(f)));
  expect(validate).toBeDefined();
  expect(validate).not.toBe(addFk);
});

test("ANSWER.md explains the lock queue", () => {
  const a = fs.readFileSync(path.join(ROOT, "ANSWER.md"), "utf8").toLowerCase();
  expect(a).toMatch(/lock queue|queued behind|waiting behind|queue behind/);
  expect(a).toMatch(/idle in transaction/);
});
