"""Load a Salesforce-shaped CSV export into the Keystone pilot database (SQLite)."""

from __future__ import annotations

import csv
import logging
import sqlite3
from pathlib import Path

from .ids import canonical_id

log = logging.getLogger("keystone_import")

SCHEMA = """
CREATE TABLE IF NOT EXISTS accounts (
  pk INTEGER PRIMARY KEY,
  sf_id18 TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  industry TEXT,
  region TEXT,
  partner_tier TEXT
);
CREATE TABLE IF NOT EXISTS contacts (
  pk INTEGER PRIMARY KEY,
  sf_id18 TEXT NOT NULL UNIQUE,
  account_pk INTEGER NOT NULL REFERENCES accounts(pk),
  first_name TEXT, last_name TEXT NOT NULL, email TEXT,
  source TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS opportunities (
  pk INTEGER PRIMARY KEY,
  sf_id18 TEXT NOT NULL UNIQUE,
  account_pk INTEGER NOT NULL REFERENCES accounts(pk),
  name TEXT NOT NULL, stage TEXT NOT NULL, amount REAL
);
CREATE TABLE IF NOT EXISTS tasks (
  pk INTEGER PRIMARY KEY,
  sf_id18 TEXT NOT NULL UNIQUE,
  who_contact_pk INTEGER REFERENCES contacts(pk),
  what_account_pk INTEGER REFERENCES accounts(pk),
  what_opportunity_pk INTEGER REFERENCES opportunities(pk),
  subject TEXT
);
CREATE TABLE IF NOT EXISTS rejects (
  object TEXT NOT NULL, sf_id TEXT NOT NULL, reason TEXT NOT NULL,
  PRIMARY KEY (object, sf_id)
);
"""


def read_csv(path: Path) -> list[dict]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        log.warning("encoding: UTF-8 BOM detected in %s, stripped", path.name)
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _reject(db: sqlite3.Connection, obj: str, sf_id: str, reason: str) -> None:
    db.execute("INSERT OR REPLACE INTO rejects(object, sf_id, reason) VALUES (?, ?, ?)", (obj, sf_id, reason))
    log.warning("reject %s %s: %s", obj, sf_id, reason)


def _pk(db: sqlite3.Connection, table: str, raw_id: str) -> int | None:
    if not raw_id:
        return None
    row = db.execute(f"SELECT pk FROM {table} WHERE sf_id18 = ?", (canonical_id(raw_id),)).fetchone()
    return row[0] if row else None


def import_export(export_dir: str | Path, db_path: str | Path) -> dict:
    """Import every object; safe to re-run (upsert by legacy id). Returns per-object counts."""
    export_dir = Path(export_dir)
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    counts = {"Account": 0, "Contact": 0, "Opportunity": 0, "Task": 0}

    for r in read_csv(export_dir / "Account.csv"):
        if not r["Name"].strip():
            _reject(db, "Account", r["Id"], "missing required Name")
            continue
        db.execute(
            """INSERT INTO accounts(sf_id18, name, industry, region, partner_tier) VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(sf_id18) DO UPDATE SET name = excluded.name, industry = excluded.industry,
                 region = excluded.region, partner_tier = excluded.partner_tier""",
            (canonical_id(r["Id"]), r["Name"], r["Industry"], r["Region__c"], r["Partner_Tier__c"]),
        )
        counts["Account"] += 1

    contact_files = [(export_dir / "Contact.csv", "crm"), (export_dir / "partner_portal" / "Contact.csv", "partner_portal")]
    for path, source in contact_files:
        for r in read_csv(path):
            acct = _pk(db, "accounts", r["AccountId"])
            if acct is None:
                _reject(db, "Contact", r["Id"], "parent Account not imported")
                continue
            db.execute(
                """INSERT INTO contacts(sf_id18, account_pk, first_name, last_name, email, source) VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(sf_id18) DO UPDATE SET account_pk = excluded.account_pk, first_name = excluded.first_name,
                     last_name = excluded.last_name, email = excluded.email, source = excluded.source""",
                (canonical_id(r["Id"]), acct, r["FirstName"], r["LastName"], r["Email"], source),
            )
            counts["Contact"] += 1

    for r in read_csv(export_dir / "Opportunity.csv"):
        acct = _pk(db, "accounts", r["AccountId"])
        if acct is None:
            _reject(db, "Opportunity", r["Id"], "parent Account not imported")
            continue
        db.execute(
            """INSERT INTO opportunities(sf_id18, account_pk, name, stage, amount) VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(sf_id18) DO UPDATE SET account_pk = excluded.account_pk, name = excluded.name,
                 stage = excluded.stage, amount = excluded.amount""",
            (canonical_id(r["Id"]), acct, r["Name"], r["StageName"], float(r["Amount"] or 0)),
        )
        counts["Opportunity"] += 1

    for r in read_csv(export_dir / "Task.csv"):
        who = _pk(db, "contacts", r["WhoId"])
        what_id = r["WhatId"]
        what_acct = _pk(db, "accounts", what_id) if what_id.startswith("001") else None
        what_opp = _pk(db, "opportunities", what_id) if what_id.startswith("006") else None
        if (r["WhoId"] and who is None) or (what_id and what_acct is None and what_opp is None):
            _reject(db, "Task", r["Id"], "WhoId/WhatId parent not imported")
            continue
        db.execute(
            """INSERT INTO tasks(sf_id18, who_contact_pk, what_account_pk, what_opportunity_pk, subject) VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(sf_id18) DO UPDATE SET who_contact_pk = excluded.who_contact_pk,
                 what_account_pk = excluded.what_account_pk, what_opportunity_pk = excluded.what_opportunity_pk,
                 subject = excluded.subject""",
            (canonical_id(r["Id"]), who, what_acct, what_opp, r["Subject"]),
        )
        counts["Task"] += 1

    db.commit()
    db.close()
    log.info("import done: %s", counts)
    return counts
