"""SQLite window table used by the plant dashboard."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS windows (
  device_id    TEXT NOT NULL,
  window_start TEXT NOT NULL,
  rms          REAL NOT NULL,
  asset_tag    TEXT NOT NULL,
  PRIMARY KEY (device_id, window_start)
);
"""


class WindowStore:
    def __init__(self, path: str | Path) -> None:
        self.conn = sqlite3.connect(str(path), isolation_level=None)
        self.conn.executescript(SCHEMA)
        self.transactions = 0

    def write_rows(self, rows: list[tuple[str, str, float, str]]) -> int:
        """Write (device_id, window_start, rms, asset_tag) rows in one transaction; idempotent per window."""
        self.conn.execute("BEGIN")
        try:
            self.conn.executemany(
                "INSERT INTO windows VALUES (?, ?, ?, ?)"
                " ON CONFLICT (device_id, window_start) DO UPDATE SET rms=excluded.rms, asset_tag=excluded.asset_tag",
                rows,
            )
        except BaseException:
            self.conn.execute("ROLLBACK")
            raise
        self.conn.execute("COMMIT")
        self.transactions += 1
        return len(rows)

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM windows").fetchone()[0]

    def distinct(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM (SELECT DISTINCT device_id, window_start FROM windows)").fetchone()[0]

    def per_device_hour(self) -> list[tuple[str, str, int]]:
        return list(self.conn.execute(
            "SELECT device_id, substr(window_start, 1, 13) AS hour, COUNT(*) FROM windows GROUP BY 1, 2 ORDER BY 1, 2"))

    def close(self) -> None:
        self.conn.close()
