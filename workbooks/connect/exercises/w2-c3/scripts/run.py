"""Print a query's result: python scripts/run.py queries/q1_weekly_volume_by_driver.sql [limit]"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db import connect, run_file  # noqa: E402

con = connect(Path(__file__).resolve().parent.parent / "data")
cols, rows = run_file(con, sys.argv[1])
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 40
print(" | ".join(cols))
for r in rows[:limit]:
    print(" | ".join("" if v is None else str(v) for v in r))
if len(rows) > limit:
    print(f"... {len(rows)} rows")
