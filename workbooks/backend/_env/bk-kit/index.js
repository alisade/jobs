"use strict";
// In-process PostgreSQL for the workbook: PGlite is PostgreSQL (18.x) compiled to WebAssembly.
// It runs the real planner, RLS, constraints and EXPLAIN, in one process and one connection,
// with no server and no network. Limits: a single session (no concurrent transactions, so no
// real lock waits), and timings in EXPLAIN ANALYZE are WASM timings, not production timings.
const fs = require("fs");
const path = require("path");

async function openDb() {
  const { PGlite } = require("@electric-sql/pglite");
  const db = new PGlite();
  await db.waitReady;
  return db;
}

function readSql(file) {
  return fs.readFileSync(path.resolve(file), "utf8");
}

async function runSqlFile(db, file) {
  await db.exec(readSql(file));
}

// Apply every *.sql file in a directory in lexical order (migrations/0001_x.sql ...).
async function applyDir(db, dir) {
  const files = fs.readdirSync(dir).filter((f) => f.endsWith(".sql")).sort();
  for (const f of files) {
    try {
      await db.exec(readSql(path.join(dir, f)));
    } catch (e) {
      e.message = `${f}: ${e.message}`;
      throw e;
    }
  }
  return files;
}

// EXPLAIN a statement and return the plan as one string (FORMAT TEXT).
async function explain(db, sql, params = [], opts = "") {
  const r = await db.query(`EXPLAIN ${opts ? "(" + opts + ") " : ""}${sql}`, params);
  return r.rows.map((row) => row["QUERY PLAN"]).join("\n");
}

module.exports = { openDb, readSql, runSqlFile, applyDir, explain };
