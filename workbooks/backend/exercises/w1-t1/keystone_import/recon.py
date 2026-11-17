"""Reconciliation report: source export vs Keystone pilot database.

Per object: source rows, rejected rows (with reasons), expected = source - rejected, target rows,
and a checksum over normalized business fields on both sides. Orphan checks look for target rows
whose parent is missing. `unexplained` counts every mismatch that the reject list does not explain.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from .ids import canonical_id
from .importer import read_csv


def _digest(rows: list[tuple]) -> str:
    h = hashlib.sha256()
    for row in sorted(rows):
        h.update(json.dumps(row, separators=(",", ":")).encode())
    return h.hexdigest()[:16]


def _norm(v: str | None) -> str:
    return (v or "").strip()


def build_report(export_dir: str | Path, db_path: str | Path) -> dict:
    export_dir = Path(export_dir)
    db = sqlite3.connect(db_path)
    rejects = {(o, canonical_id(i)): reason for o, i, reason in db.execute("SELECT object, sf_id, reason FROM rejects")}

    def accepted(obj: str, rows: list[dict]) -> list[dict]:
        return [r for r in rows if (obj, canonical_id(r["Id"])) not in rejects]

    src_acc = read_csv(export_dir / "Account.csv")
    src_con = read_csv(export_dir / "Contact.csv") + read_csv(export_dir / "partner_portal" / "Contact.csv")
    src_opp = read_csv(export_dir / "Opportunity.csv")
    src_task = read_csv(export_dir / "Task.csv")

    source_sums = {
        "Account": [(canonical_id(r["Id"]), _norm(r["Name"])) for r in accepted("Account", src_acc)],
        "Contact": [(canonical_id(r["Id"]), canonical_id(r["AccountId"]), _norm(r["Email"]).lower()) for r in accepted("Contact", src_con)],
        "Opportunity": [(canonical_id(r["Id"]), canonical_id(r["AccountId"]), _norm(r["StageName"])) for r in accepted("Opportunity", src_opp)],
        "Task": [(canonical_id(r["Id"]), _norm(r["Subject"])) for r in accepted("Task", src_task)],
    }
    target_sums = {
        "Account": [tuple(r) for r in db.execute("SELECT sf_id18, name FROM accounts")],
        "Contact": [tuple(r) for r in db.execute(
            "SELECT c.sf_id18, a.sf_id18, lower(trim(coalesce(c.email, ''))) FROM contacts c JOIN accounts a ON a.pk = c.account_pk")],
        "Opportunity": [tuple(r) for r in db.execute(
            "SELECT o.sf_id18, a.sf_id18, o.stage FROM opportunities o JOIN accounts a ON a.pk = o.account_pk")],
        "Task": [tuple(r) for r in db.execute("SELECT sf_id18, coalesce(subject, '') FROM tasks")],
    }
    sources = {"Account": src_acc, "Contact": src_con, "Opportunity": src_opp, "Task": src_task}
    tables = {"Account": "accounts", "Contact": "contacts", "Opportunity": "opportunities", "Task": "tasks"}

    objects = {}
    unexplained = 0
    for obj in sources:
        rej = sum(1 for (o, _i) in rejects if o == obj)
        target = db.execute(f"SELECT count(*) FROM {tables[obj]}").fetchone()[0]
        expected = len(sources[obj]) - rej
        match = _digest(source_sums[obj]) == _digest(target_sums[obj])
        objects[obj] = {"source": len(sources[obj]), "rejected": rej, "expected": expected, "target": target,
                        "count_match": expected == target, "checksum_match": match}
        unexplained += abs(expected - target) + (0 if match else 1)

    orphans = {
        "contacts_without_account": db.execute(
            "SELECT count(*) FROM contacts c LEFT JOIN accounts a ON a.pk = c.account_pk WHERE a.pk IS NULL").fetchone()[0],
        "tasks_without_parent": db.execute(
            """SELECT count(*) FROM tasks t WHERE (t.who_contact_pk IS NOT NULL AND t.who_contact_pk NOT IN (SELECT pk FROM contacts))
               OR (t.what_account_pk IS NOT NULL AND t.what_account_pk NOT IN (SELECT pk FROM accounts))
               OR (t.what_opportunity_pk IS NOT NULL AND t.what_opportunity_pk NOT IN (SELECT pk FROM opportunities))""").fetchone()[0],
    }
    unexplained += sum(orphans.values())
    reject_list = [{"object": o, "id": i, "reason": r} for o, i, r in db.execute("SELECT object, sf_id, reason FROM rejects ORDER BY 1, 2")]
    db.close()
    return {"objects": objects, "orphans": orphans, "rejects": reject_list, "unexplained": unexplained}


def render(report: dict) -> str:
    lines = ["object        source  rejected  expected  target  counts  checksum"]
    for obj, o in report["objects"].items():
        lines.append(f"{obj:<12} {o['source']:>7} {o['rejected']:>9} {o['expected']:>9} {o['target']:>7}  "
                     f"{'ok' if o['count_match'] else 'DIFF':>6}  {'ok' if o['checksum_match'] else 'DIFF':>8}")
    lines.append("orphans: " + ", ".join(f"{k}={v}" for k, v in report["orphans"].items()))
    lines.append(f"rejected rows: {len(report['rejects'])}")
    for r in report["rejects"]:
        lines.append(f"  {r['object']:<12} {r['id']}  {r['reason']}")
    lines.append(f"UNEXPLAINED MISMATCHES: {report['unexplained']}")
    return "\n".join(lines)
