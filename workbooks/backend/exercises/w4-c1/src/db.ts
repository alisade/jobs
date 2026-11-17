// Database access for pipeline-svc. In production this is a pg Pool behind PgBouncer; here it is
// PGlite (PostgreSQL 18 in process) with the same SQL. The Kysely PGlite driver serializes
// connections, so concurrent requests queue for the one session, much like a pool of size 1.
import * as fs from "fs";
import * as path from "path";
import { Kysely, sql, Transaction, KyselyConfig } from "kysely";
import { PGliteDialect } from "kysely-pglite-dialect";
import type { PGlite } from "@electric-sql/pglite";
import { openDb } from "bk-kit";
import type { Database } from "./types";

export interface Db { pg: PGlite; db: Kysely<Database> }

export async function openDatabase(log?: KyselyConfig["log"]): Promise<Db> {
  const pg = await openDb();
  const dir = path.resolve(__dirname, "..", "migrations");
  for (const f of fs.readdirSync(dir).filter((x) => x.endsWith(".sql")).sort()) {
    await pg.exec(fs.readFileSync(path.join(dir, f), "utf8"));
  }
  const db = new Kysely<Database>({ dialect: new PGliteDialect(pg), log });
  return { pg, db };
}

// Run fn in one transaction as the application role with the tenant set for this transaction only
// (set_config(..., true) is SET LOCAL: it cannot leak to the next request on a pooled connection).
export async function withTenant<T>(db: Kysely<Database>, tenantId: string, fn: (trx: Transaction<Database>) => Promise<T>): Promise<T> {
  return db.transaction().execute(async (trx) => {
    await sql`SET LOCAL ROLE pipeline_app`.execute(trx);
    await sql`SELECT set_config('app.tenant_id', ${tenantId}, true)`.execute(trx);
    return fn(trx);
  });
}
