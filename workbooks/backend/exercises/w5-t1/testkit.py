"""Test helpers."""
from outbox.db import connect


def effects(consumer_db: str) -> int:
    conn = connect(consumer_db)
    n = conn.execute("SELECT count(*) FROM stage_changes").fetchone()[0]
    conn.close()
    return n


def statuses(db: str) -> dict:
    conn = connect(db)
    out = {r[0]: r[1] for r in conn.execute("SELECT status, count(*) FROM outbox GROUP BY status")}
    conn.close()
    return out
