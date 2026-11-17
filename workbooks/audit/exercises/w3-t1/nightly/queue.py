"""Reviewer work queue (the GRC review inbox), a SQLite table outside ADK. Do not edit."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS work_items (id INTEGER PRIMARY KEY, change_id TEXT, kind TEXT, created_by TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS tested (change_id TEXT, invocation TEXT)")
    return db


def counts(path: Path) -> dict:
    db = connect(path)
    tested = db.execute("SELECT change_id, COUNT(*) FROM tested GROUP BY change_id").fetchall()
    items = db.execute("SELECT change_id, COUNT(*) FROM work_items GROUP BY change_id").fetchall()
    return {"tested": dict(tested), "work_items": dict(items)}
