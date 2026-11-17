"""Schema migrations (Flyway-style, V<n>__name.sql applied in order, checksums recorded). Do not change."""

from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"


def migrations(folder: Path = MIGRATIONS) -> list[tuple[int, Path]]:
    out = []
    for p in folder.glob("V*__*.sql"):
        m = re.match(r"V(\d+)__", p.name)
        if m:
            out.append((int(m.group(1)), p))
    return sorted(out)


def migrate(conn: sqlite3.Connection, folder: Path = MIGRATIONS) -> list[str]:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_history (version INTEGER PRIMARY KEY, script TEXT, checksum TEXT)")
    done = {v: c for v, c in conn.execute("SELECT version, checksum FROM schema_history")}
    applied = []
    for v, p in migrations(folder):
        sql = p.read_text()
        cs = hashlib.sha256(sql.encode()).hexdigest()
        if v in done:
            if done[v] != cs:
                raise RuntimeError(f"checksum mismatch for applied migration {p.name}: never edit an applied migration")
            continue
        conn.executescript(sql)
        conn.execute("INSERT INTO schema_history VALUES (?, ?, ?)", (v, p.name, cs))
        applied.append(p.name)
    conn.commit()
    return applied
