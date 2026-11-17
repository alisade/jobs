// kmigrate-lint: the checks Lumenfold adopted after the 2026-11-12 incident (squawk-style, stdlib only).
// Applies to migrations numbered 0057 and up (older files are grandfathered).
// Usage: node scripts/lint.js [dir]     exit 1 when any error is found.
"use strict";
const fs = require("fs");
const path = require("path");

const FIRST_CHECKED = 57;

function splitStatements(text) {
  return text.split(/;\s*$/m).map((s) => s.replace(/^\s*--.*$/gm, "").replace(/\s+/g, " ").trim()).filter(Boolean);
}

function lintFile(name, text, state) {
  const out = [];
  const err = (i, rule, msg) => out.push({ file: name, stmt: i + 1, level: "error", rule, msg });
  const warn = (i, rule, msg) => out.push({ file: name, stmt: i + 1, level: "warning", rule, msg });
  const noTx = /^--\s*kmigrate:no-transaction/.test(text);
  const stmts = splitStatements(text);
  const createdHere = new Set();
  let lockTimeout = false;
  let stmtTimeout = false;
  const addedNotValid = new Set();
  stmts.forEach((s, i) => {
    const u = s.toUpperCase();
    if (/^(BEGIN|COMMIT|START TRANSACTION|END)\b/.test(u)) err(i, "no-explicit-transaction", "kmigrate manages transactions; remove BEGIN/COMMIT");
    if (/^SET (LOCAL )?LOCK_TIMEOUT\b/.test(u)) { lockTimeout = true; return; }
    if (/^SET (LOCAL )?STATEMENT_TIMEOUT\b/.test(u)) { stmtTimeout = true; return; }
    const ct = u.match(/^CREATE TABLE (IF NOT EXISTS )?("?[\w.]+"?)/);
    if (ct) { createdHere.add(ct[2].replace(/"/g, "").toLowerCase()); return; }
    const isIndex = /^CREATE (UNIQUE )?INDEX\b/.test(u);
    const isAlter = /^ALTER TABLE\b/.test(u);
    if ((isIndex || isAlter) && !lockTimeout) {
      err(i, "require-lock-timeout", "SET lock_timeout before DDL so a blocked migration fails fast instead of queueing every query behind it");
    }
    if ((isIndex || isAlter) && !stmtTimeout && !/CONCURRENTLY/.test(u)) {
      warn(i, "require-statement-timeout", "consider SET statement_timeout for DDL that scans the table");
    }
    if (isIndex) {
      const t = (u.match(/ ON (ONLY )?("?[\w.]+"?)/) || [])[2];
      const table = t ? t.replace(/"/g, "").toLowerCase() : "";
      if (!/CONCURRENTLY/.test(u) && !createdHere.has(table)) {
        err(i, "index-concurrently", `CREATE INDEX on existing table ${table} must use CONCURRENTLY (a plain build blocks writes for the whole build)`);
      }
      if (/CONCURRENTLY/.test(u) && !noTx) {
        err(i, "concurrently-outside-transaction", "CREATE INDEX CONCURRENTLY cannot run in a transaction: start the file with -- kmigrate:no-transaction");
      }
    }
    if (noTx && !isIndex && !/^SET\b/.test(u) && !/^(DROP|REINDEX) .*CONCURRENTLY/.test(u)) {
      err(i, "no-transaction-only-concurrent", "a no-transaction migration should contain only SET and CONCURRENTLY statements; move other DDL to its own migration");
    }
    if (isAlter) {
      const t = (u.match(/^ALTER TABLE (ONLY )?(IF EXISTS )?("?[\w.]+"?)/) || [])[3];
      const table = t ? t.replace(/"/g, "").toLowerCase() : "";
      const add = u.match(/ADD CONSTRAINT ("?\w+"?) (FOREIGN KEY|CHECK)/);
      if (add && !createdHere.has(table)) {
        const cname = add[1].replace(/"/g, "").toLowerCase();
        if (!/NOT VALID/.test(u)) {
          err(i, "constraint-not-valid", `ADD CONSTRAINT ${cname} on existing table ${table}: add it NOT VALID, then VALIDATE CONSTRAINT in a later migration`);
        } else {
          addedNotValid.add(cname);
          state.notValid.add(cname);
        }
      }
      const v = u.match(/VALIDATE CONSTRAINT ("?\w+"?)/);
      if (v) {
        const cname = v[1].replace(/"/g, "").toLowerCase();
        if (addedNotValid.has(cname)) err(i, "validate-in-separate-migration", `VALIDATE CONSTRAINT ${cname} in the same migration as ADD ... NOT VALID holds the lock for the whole scan`);
        state.validated.add(cname);
      }
      if (/ALTER COLUMN .* (TYPE|SET NOT NULL)\b/.test(u) && !createdHere.has(table)) {
        err(i, "no-blocking-alter-column", "ALTER COLUMN TYPE / SET NOT NULL rewrites or scans under ACCESS EXCLUSIVE; use expand/contract");
      }
    }
  });
  return out;
}

function lintDir(dir) {
  const state = { notValid: new Set(), validated: new Set() };
  const files = fs.readdirSync(dir).filter((f) => /^\d{4}_.+\.sql$/.test(f)).sort();
  let results = [];
  for (const f of files) {
    if (Number(f.slice(0, 4)) < FIRST_CHECKED) continue;
    results = results.concat(lintFile(f, fs.readFileSync(path.join(dir, f), "utf8"), state));
  }
  for (const c of state.notValid) {
    if (!state.validated.has(c)) results.push({ file: "-", stmt: 0, level: "warning", rule: "not-valid-never-validated", msg: `${c} is NOT VALID and never validated` });
  }
  return results;
}

module.exports = { lintDir, lintFile, splitStatements };

if (require.main === module) {
  const dir = process.argv[2] || path.resolve(__dirname, "..", "migrations");
  const res = lintDir(dir);
  for (const r of res) console.log(`${r.level.padEnd(8)} ${r.file}:${r.stmt}  ${r.rule}  ${r.msg}`);
  const errors = res.filter((r) => r.level === "error").length;
  console.log(errors ? `${errors} error(s)` : "lint clean");
  process.exit(errors ? 1 : 0);
}
