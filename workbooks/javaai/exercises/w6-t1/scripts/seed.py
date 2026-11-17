"""Create a database with the schema and synthetic data.  python scripts/seed.py <db> [attempts]"""

import random
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dashboard.db import migrate  # noqa: E402


def seed(path: str, attempts: int = 200_000, seed: int = 11) -> None:
    rnd = random.Random(seed)
    p = Path(path)
    if p.exists():
        p.unlink()
    conn = sqlite3.connect(path)
    migrate(conn)
    courses = [f"c{i:02d}" for i in range(12)]
    conn.executemany("INSERT INTO course VALUES (?, ?)", [(c, f"Course {c}") for c in courses])
    learners = [f"lrn-{i:05d}" for i in range(4000)]
    conn.executemany("INSERT INTO learner (id, email, created_at) VALUES (?, ?, ?)",
                     [(l, f"{l}@example.edu", "2026-08-01T00:00:00Z") for l in learners])
    items = [(i, courses[i % 12], f"l{i % 9}", f"stem {i}") for i in range(1, 2401)]
    conn.executemany("INSERT INTO quiz_item VALUES (?, ?, ?, ?)", items)
    start = datetime(2026, 8, 25, tzinfo=timezone.utc)
    rows = []
    for i in range(attempts):
        it = items[rnd.randrange(len(items))]
        ts = start + timedelta(seconds=rnd.randrange(80 * 86400))
        rows.append((i + 1, learners[rnd.randrange(len(learners))], it[0], it[1], rnd.randrange(4), rnd.random() < 0.7,
                     ts.strftime("%Y-%m-%dT%H:%M:%SZ")))
    conn.executemany("INSERT INTO quiz_attempt VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    seed(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 200_000)
