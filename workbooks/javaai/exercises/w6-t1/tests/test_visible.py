import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from seed import seed  # noqa: E402

from dashboard import queries  # noqa: E402


def test_query_returns_recent_rows(tmp_path):
    db = tmp_path / "t.db"
    seed(str(db), 5000)
    conn = sqlite3.connect(db)
    rows = queries.recent_attempts(conn, "lrn-00007", "c07", "2026-08-01")
    assert all(rows[i][3] >= rows[i + 1][3] for i in range(len(rows) - 1))
