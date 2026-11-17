import type { PGlite } from "@electric-sql/pglite";
export function openDb(): Promise<PGlite>;
export function readSql(file: string): string;
export function runSqlFile(db: PGlite, file: string): Promise<void>;
export function applyDir(db: PGlite, dir: string): Promise<string[]>;
export function explain(db: PGlite, sql: string, params?: unknown[], opts?: string): Promise<string>;
