"""SQLite checkpoint store. Complete; use it from run.py.

One row per (run_id, sample_id, step) holds that step's JSON output once the step is committed.
``put_step`` is INSERT-only: committing the same step twice is a bug in the caller and raises.
Samples have a state column the orchestrator moves forward.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS samples (
  run_id TEXT NOT NULL, sample_id TEXT NOT NULL, state TEXT NOT NULL,
  PRIMARY KEY (run_id, sample_id));
CREATE TABLE IF NOT EXISTS steps (
  run_id TEXT NOT NULL, sample_id TEXT NOT NULL, step TEXT NOT NULL, output TEXT NOT NULL,
  PRIMARY KEY (run_id, sample_id, step));
"""


class CheckpointStore:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.db = sqlite3.connect(self.path, isolation_level=None, timeout=5)
        self.db.executescript(SCHEMA)

    def close(self) -> None:
        self.db.close()

    # samples
    def add_sample(self, run_id: str, sample_id: str) -> None:
        self.db.execute("INSERT OR IGNORE INTO samples VALUES (?, ?, 'pending')", (run_id, sample_id))

    def state(self, run_id: str, sample_id: str) -> str | None:
        row = self.db.execute("SELECT state FROM samples WHERE run_id=? AND sample_id=?", (run_id, sample_id)).fetchone()
        return row[0] if row else None

    def set_state(self, run_id: str, sample_id: str, state: str) -> None:
        self.db.execute("UPDATE samples SET state=? WHERE run_id=? AND sample_id=?", (state, run_id, sample_id))

    def samples(self, run_id: str) -> list[tuple[str, str]]:
        return [tuple(r) for r in self.db.execute(
            "SELECT sample_id, state FROM samples WHERE run_id=? ORDER BY sample_id", (run_id,))]

    # steps
    def get_step(self, run_id: str, sample_id: str, step: str) -> Any | None:
        row = self.db.execute("SELECT output FROM steps WHERE run_id=? AND sample_id=? AND step=?",
                              (run_id, sample_id, step)).fetchone()
        return json.loads(row[0]) if row else None

    def put_step(self, run_id: str, sample_id: str, step: str, output: Any, *, state: str | None = None) -> None:
        """Commit a step output (and optionally the new sample state) in one transaction."""
        with self.db:
            self.db.execute("BEGIN")
            self.db.execute("INSERT INTO steps VALUES (?, ?, ?, ?)",
                            (run_id, sample_id, step, json.dumps(output, sort_keys=True)))
            if state is not None:
                self.db.execute("UPDATE samples SET state=? WHERE run_id=? AND sample_id=?", (state, run_id, sample_id))
