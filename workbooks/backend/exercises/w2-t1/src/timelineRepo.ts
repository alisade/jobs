// pipeline-svc: account timeline repository (2026.44).
import * as path from "path";
import type { PGlite } from "@electric-sql/pglite";
// eslint-disable-next-line @typescript-eslint/no-var-requires
const { kdbQuery, loadQuery } = require("../scripts/db.js");

export interface TimelineRow { id: number; type: string; subject: string; occurred_at: Date }
export interface Cursor { occurredAt: string; id: string }

const SQL_FILE = path.resolve(__dirname, "..", "queries", "timeline.sql");
const FIRST_PAGE: Cursor = { occurredAt: "infinity", id: "9223372036854775807" };

export async function timelinePage(db: PGlite, tenantId: string, accountId: string, after: Cursor = FIRST_PAGE): Promise<TimelineRow[]> {
  const sql = loadQuery(SQL_FILE);
  const r = await kdbQuery(db, sql, [tenantId, accountId, after.occurredAt, after.id]);
  return r.rows as TimelineRow[];
}

export function nextCursor(rows: TimelineRow[]): Cursor | null {
  if (rows.length === 0) return null;
  const last = rows[rows.length - 1];
  return { occurredAt: new Date(last.occurred_at).toISOString(), id: String(last.id) };
}
