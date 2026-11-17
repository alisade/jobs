// Test helpers for backend/w4-c1: a fresh database + app per test, seeded as the superuser.
import type { FastifyInstance } from "fastify";
import type { KyselyConfig } from "kysely";
import { openDatabase, Db } from "../src/db";
import { buildApp, Hooks } from "../src/app";

export const SEED = `
INSERT INTO opportunities (tenant_id, account_id, owner_id, name, stage, amount, close_date, version) VALUES
  ('bu-emea', 101, 'u-priya', 'Orbital Freight renewal',  'prospecting', 0,     NULL,         1),
  ('bu-emea', 101, 'u-priya', 'Orbital Freight expansion','negotiation', 50000, NULL,         3),
  ('bu-emea', 102, 'u-dana',  'Harbor Labs pilot',        'negotiation', 0,     NULL,         1),
  ('bu-amer', 201, 'u-tomas', 'Cedar Grid platform',      'qualification', 9000, NULL,        1),
  ('bu-emea', 103, 'u-dana',  'Fjord Retail',             'closed_lost', 1200,  '2026-09-30', 2),
  ('bu-emea', 104, 'u-priya', 'Northgate analytics',      'proposal',    1000,  NULL,         1);
`;

export interface Ctx { db: Db; app: FastifyInstance; sqlLog: string[] }

export async function start(hooks?: Hooks, configure?: (app: FastifyInstance) => void): Promise<Ctx> {
  const sqlLog: string[] = [];
  const log: KyselyConfig["log"] = (e) => { if (e.level === "query") sqlLog.push(e.query.sql); };
  const db = await openDatabase(log);
  await db.pg.exec(SEED);
  const app = buildApp({ db, hooks });
  if (configure) configure(app);   // e.g. installGracefulShutdown, before the app boots
  await app.ready();
  return { db, app, sqlLog };
}

export async function stop(ctx?: Ctx): Promise<void> {
  if (!ctx) return;
  try { await ctx.app.close(); } catch { /* already closed */ }
  try { await ctx.db.pg.close(); } catch { /* already closed */ }
}

export function transition(ctx: Ctx, id: number | string, body: unknown, tenant: string | null = "bu-emea") {
  const headers: Record<string, string> = { "content-type": "application/json", "x-user-id": "u-priya" };
  if (tenant) headers["x-tenant-id"] = tenant;
  return ctx.app.inject({ method: "POST", url: `/v1/opportunities/${id}/transitions`, headers, payload: JSON.stringify(body) });
}

export async function rows<T = Record<string, unknown>>(ctx: Ctx, sql: string, params: unknown[] = []): Promise<T[]> {
  return (await ctx.db.pg.query<T>(sql, params)).rows;
}
