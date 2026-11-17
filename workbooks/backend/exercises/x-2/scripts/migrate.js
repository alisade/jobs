// kmigrate (Lumenfold's migration runner), reproduced for PGlite.
// - Applies migrations/NNNN_*.sql in order and records them in schema_migrations.
// - Each file runs in ONE transaction, unless its first line is `-- kmigrate:no-transaction`; then
//   each statement (split on ';' at end of line) runs on its own, outside any transaction, which is
//   what CREATE INDEX CONCURRENTLY needs.
// - Files must not contain BEGIN/COMMIT themselves.
// Usage: node scripts/migrate.js            (fresh database: baseline, seed, then the rest)
"use strict";
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const BASELINE_MAX = 56;

function listMigrations(dir) {
  return fs.readdirSync(dir).filter((f) => /^\d{4}_.+\.sql$/.test(f)).sort();
}

function statements(text) {
  return text.split(/;\s*$/m).map((s) => s.replace(/^\s*--.*$/gm, "").trim()).filter(Boolean);
}

async function applyFile(db, file) {
  const text = fs.readFileSync(file, "utf8");
  const noTx = /^--\s*kmigrate:no-transaction/.test(text);
  if (noTx) {
    for (const stmt of statements(text)) await db.exec(stmt);
  } else {
    await db.exec("BEGIN;\n" + text + "\nCOMMIT;");
  }
  await db.query("INSERT INTO schema_migrations (version) VALUES ($1)", [path.basename(file)]);
  return noTx;
}

// Applies all migrations; runs seedSql right after the baseline (files numbered <= 0056).
async function migrate(db, { dir = path.join(ROOT, "migrations"), seedSql = null, log = () => {} } = {}) {
  await db.exec("CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())");
  let seeded = false;
  for (const f of listMigrations(dir)) {
    const n = Number(f.slice(0, 4));
    if (!seeded && seedSql && n > BASELINE_MAX) { await db.exec(seedSql); seeded = true; log("seeded"); }
    try {
      const noTx = await applyFile(db, path.join(dir, f));
      log(`applied ${f}${noTx ? " (no transaction)" : ""}`);
    } catch (e) {
      try { await db.exec("ROLLBACK;"); } catch { /* not in a transaction */ }
      e.message = `${f}: ${e.message}`;
      throw e;
    }
  }
  if (!seeded && seedSql) await db.exec(seedSql);
}

module.exports = { migrate, listMigrations, statements, ROOT };

if (require.main === module) {
  (async () => {
    const { openDb } = require("bk-kit");
    const db = await openDb();
    await migrate(db, { seedSql: fs.readFileSync(path.join(ROOT, "scripts", "seed.sql"), "utf8"), log: (m) => console.log(m) });
    const c = await db.query("SELECT conname, convalidated FROM pg_constraint WHERE conrelid = 'activities'::regclass AND contype = 'f' ORDER BY 1");
    const i = await db.query("SELECT indexrelid::regclass::text AS index, indisvalid FROM pg_index WHERE indrelid = 'activities'::regclass ORDER BY 1");
    console.log("foreign keys on activities:", JSON.stringify(c.rows));
    console.log("indexes on activities:", JSON.stringify(i.rows));
    await db.close();
  })().catch((e) => { console.error("migrate failed: " + e.message); process.exit(1); });
}
