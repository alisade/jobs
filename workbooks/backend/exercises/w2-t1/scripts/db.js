// Shared by make explain, the incident generator and the tests: a fresh in-process PostgreSQL
// (PGlite) with the schema and the synthetic seed, and the kdb-style query call the service uses.
"use strict";
const fs = require("fs");
const path = require("path");
const { openDb, applyDir } = require("bk-kit");

const ROOT = path.resolve(__dirname, "..");
const TEXT_OID = 25;

async function openSeeded() {
  const db = await openDb();
  await applyDir(db, path.join(ROOT, "migrations"));
  await db.exec(fs.readFileSync(path.join(ROOT, "scripts", "seed.sql"), "utf8"));
  return db;
}

// kdb (Lumenfold's thin query wrapper) declares every string parameter as text, so a prepared
// statement gets the same parameter types whatever the caller passes. Reproduced here.
function kdbQuery(db, sql, params, prefix = "") {
  return db.query(prefix + sql, params, { paramTypes: params.map(() => TEXT_OID) });
}

function loadQuery(file) {
  return fs.readFileSync(file, "utf8").replace(/;\s*$/, "");
}

async function orbitalId(db) {
  const r = await db.query("SELECT id::text AS id FROM accounts WHERE name = 'Orbital Freight'");
  return r.rows[0].id;
}

module.exports = { ROOT, openSeeded, kdbQuery, loadQuery, orbitalId };
