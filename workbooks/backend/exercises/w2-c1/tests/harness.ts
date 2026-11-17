// Test harness for backend/w2-c1: applies migrations/ to a fresh in-process PostgreSQL (PGlite),
// seeds synthetic Keystone data as the superuser, and runs statements as keystone_app.
import * as path from "path";
import { openDb, applyDir, readSql } from "bk-kit";
import type { PGlite } from "@electric-sql/pglite";

export const exRoot = (): string => {
  // tests/ or tests/__hidden__/ -> exercise root
  let d = __dirname;
  while (!d.endsWith("/tests")) d = path.dirname(d);
  return path.dirname(d);
};
export const TENANTS = ["bu-amer", "bu-emea", "bu-apac", "app-partner-portal"];

export const SEED = `
INSERT INTO tenants (id, name) VALUES
  ('bu-amer', 'Americas'), ('bu-emea', 'EMEA'), ('bu-apac', 'APAC'), ('app-partner-portal', 'Partner portal');
INSERT INTO accounts (tenant_id, name, owner_id, sf_id, custom_fields)
SELECT (ARRAY['bu-amer','bu-emea','bu-apac','app-partner-portal'])[1 + g % 4],
       'Account ' || g, 'u' || (g % 40),
       CASE WHEN g % 2 = 0 THEN '001A0000' || lpad(g::text, 7, '0') || 'AAA' END,
       jsonb_build_object('tier', (ARRAY['gold','silver','bronze'])[1 + g % 3], 'region_code', 'R' || (g % 250))
FROM generate_series(1, 5000) g;
INSERT INTO contacts (tenant_id, account_id, first_name, last_name, email)
SELECT a.tenant_id, a.id, 'First' || g, 'Last' || g, 'person' || g || '@example.test'
FROM generate_series(1, 10000) g JOIN accounts a ON a.id = 1 + g % 5000;
INSERT INTO opportunities (tenant_id, account_id, owner_id, name, stage, amount, close_date)
SELECT a.tenant_id, a.id, 'u' || (g % 40), 'Deal ' || g,
       (ARRAY['prospecting','qualification','proposal','negotiation','closed_won','closed_lost'])[1 + g % 6],
       (g % 900) * 100, CASE WHEN g % 6 >= 4 OR g % 3 = 0 THEN date '2026-01-01' + (g % 365) END
FROM generate_series(1, 12000) g JOIN accounts a ON a.id = 1 + g % 5000;
INSERT INTO activities (tenant_id, account_id, type, subject, occurred_at)
SELECT a.tenant_id, a.id, (ARRAY['call','email','meeting','task','note'])[1 + g % 5], 'Activity ' || g,
       timestamptz '2026-11-01 00:00:00+00' - (g || ' minutes')::interval
FROM generate_series(1, 60000) g JOIN accounts a ON a.id = 1 + g % 5000;
ANALYZE;
`;

export async function freshDb(seed = true): Promise<PGlite> {
  const db = await openDb();
  await applyDir(db, path.join(exRoot(), "migrations"));
  if (seed) await db.exec(SEED);
  return db;
}

export function query(name: string): string {
  return readSql(path.join(exRoot(), "queries", name)).replace(/;\s*$/, "");
}

// Run fn inside a transaction as keystone_app with app.tenant_id set (or unset when tenant is null).
// Always rolls back, so tests do not leak state into each other.
export async function asApp<T>(db: PGlite, tenant: string | null, fn: () => Promise<T>): Promise<T> {
  await db.exec("BEGIN; SET LOCAL ROLE keystone_app;");
  try {
    if (tenant !== null) await db.query("SELECT set_config('app.tenant_id', $1, true)", [tenant]);
    return await fn();
  } finally {
    await db.exec("ROLLBACK;");
  }
}

export async function count(db: PGlite, sql: string, params: unknown[] = []): Promise<number> {
  const r = await db.query<{ n: number }>(`SELECT count(*)::int AS n FROM (${sql}) q`, params);
  return r.rows[0].n;
}

export async function plan(db: PGlite, sql: string, params: unknown[]): Promise<string> {
  const r = await db.query<Record<string, string>>(`EXPLAIN ${sql}`, params);
  return r.rows.map((x) => x["QUERY PLAN"]).join("\n");
}

export async function rejects(db: PGlite, sql: string, params: unknown[] = []): Promise<string> {
  // Runs sql in a savepoint-free transaction of its own; returns the error message ("" when it succeeded).
  await db.exec("BEGIN;");
  try {
    await db.query(sql, params);
    return "";
  } catch (e) {
    return (e as Error).message;
  } finally {
    await db.exec("ROLLBACK;");
  }
}

// Like rejects(), but as keystone_app for one tenant.
export async function appRejects(db: PGlite, tenant: string, sql: string, params: unknown[] = []): Promise<string> {
  return asApp(db, tenant, async () => {
    try {
      await db.query(sql, params);
      return "";
    } catch (e) {
      return (e as Error).message;
    }
  });
}
