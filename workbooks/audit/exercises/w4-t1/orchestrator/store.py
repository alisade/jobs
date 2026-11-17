"""SQLite checkpoint store for the publish stage."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class Checkpoints:
    def __init__(self, path: str | Path):
        self.db = sqlite3.connect(str(path), isolation_level=None)
        self.db.execute("CREATE TABLE IF NOT EXISTS steps (run_id TEXT, sample_id TEXT, step TEXT, value TEXT,"
                        " PRIMARY KEY (run_id, sample_id, step))")

    def get(self, run_id: str, sample_id: str, step: str) -> str | None:
        row = self.db.execute("SELECT value FROM steps WHERE run_id=? AND sample_id=? AND step=?",
                              (run_id, sample_id, step)).fetchone()
        return row[0] if row else None

    def put(self, run_id: str, sample_id: str, step: str, value: str = "") -> None:
        self.db.execute("INSERT OR REPLACE INTO steps VALUES (?, ?, ?, ?)", (run_id, sample_id, step, value))

    def dump(self) -> list[tuple]:
        return list(self.db.execute("SELECT run_id, sample_id, step, value FROM steps ORDER BY sample_id, step"))
