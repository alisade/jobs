"""Time the dashboard query and print its plan.  make explain"""

import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dashboard import queries  # noqa: E402
from dashboard.db import migrate  # noqa: E402

db = Path(__file__).resolve().parent.parent / "data" / "kestrel.db"
conn = sqlite3.connect(db)
print("applied now:", migrate(conn) or "nothing new")
args = ("lrn-01234", "c03", "2026-10-01")
for line in queries.plan(conn, queries.RECENT_ATTEMPTS, args):
    print("PLAN", line)
t0 = time.perf_counter()
for _ in range(50):
    rows = queries.recent_attempts(conn, *args)
print(f"{len(rows)} rows, {1000 * (time.perf_counter() - t0) / 50:.2f} ms per query")
