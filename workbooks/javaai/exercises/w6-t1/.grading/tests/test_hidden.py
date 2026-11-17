import hashlib
import re
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from seed import seed  # noqa: E402

from dashboard import queries  # noqa: E402
from dashboard.db import migrate, migrations  # noqa: E402

APPLIED = {'V1__core.sql': '1966ddb8787880478716e48c5bfadd1c67d1e61f635d237da4a6bbb5058d96f4', 'V2__attempts.sql': '5eab0926e540aa4f096e65bdcfb53b49c6383cde81e9d4a75f34bbb63564dfbc', 'V3__attempt_indexes.sql': '1845711fa9f401aa9c049a46aa62f4ab3fbfec3dad59d98eac7cf8e4678ea913', 'V4__enrollment.sql': '6ae740dfef49ae4fe3ef818d4b226a3489d8d9fb0c21e444fd2e11764e69e665', 'V5__quiz_item_index.sql': '573ae6adbb9f2a54a1dfe16ed9fb6a67b43f3e4c9f45e8dc73011946f72c09b9', 'V6__learner_locale.sql': '568a22c86fd18c0b204ab0f1b4620fbf42eacf742c27ca4b6d4668504fdbdc8f'}


@pytest.fixture(scope="module")
def conn(tmp_path_factory):
    db = tmp_path_factory.mktemp("db") / "k.db"
    seed(str(db), 30000)
    c = sqlite3.connect(db)
    migrate(c)  # applies anything after V6, like the deploy would
    return c


def test_applied_migrations_untouched():
    for name, sha in APPLIED.items():
        assert hashlib.sha256((ROOT / "migrations" / name).read_bytes()).hexdigest() == sha, f"{name} was edited"


def test_new_migration_is_additive():
    new = [p for v, p in migrations() if v > 6]
    assert new, "add the index in a new migration (V7__...)"
    for p in new:
        sql = re.sub(r"--[^\n]*", "", p.read_text()).upper()
        assert "DROP TABLE" not in sql and "DELETE" not in sql, f"{p.name} must be additive"


def test_plan_uses_an_index_for_filter_and_range(conn):
    lines = queries.plan(conn, queries.RECENT_ATTEMPTS, ("lrn-00042", "c03", "2026-10-01"))
    text = " | ".join(lines)
    assert "SEARCH a USING" in text, f"the attempts table is scanned, not searched: {text}"
    assert "learner_id=?" in text and "course_id=?" in text, f"the index must lead with the equality columns: {text}"
    assert "created_at>?" in text, f"the date predicate cannot use the index (function on the column?): {text}"
    assert "TEMP B-TREE" not in text, f"ORDER BY should come from the index: {text}"


def brute(conn, learner, course, since):
    rows = conn.execute("SELECT id, quiz_item_id, correct, created_at FROM quiz_attempt WHERE learner_id=? AND course_id=?",
                        (learner, course)).fetchall()
    rows = [r for r in rows if r[3][:10] >= since]
    rows.sort(key=lambda r: (r[3], r[0]), reverse=True)
    return rows[:20]


@pytest.mark.parametrize("learner,course,since", [("lrn-00042", "c03", "2026-10-01"), ("lrn-00007", "c07", "2026-08-01"),
                                                   ("lrn-03999", "c11", "2026-11-12"), ("lrn-00100", "c00", "2026-09-15")])
def test_results_unchanged(conn, learner, course, since):
    got = queries.recent_attempts(conn, learner, course, since)
    want = brute(conn, learner, course, since)
    assert [r[3] for r in got] == [r[3] for r in want]
    assert {r[0] for r in got} == {r[0] for r in want} or len(got) == 20


def test_boundary_day_is_inclusive(conn):
    conn.execute("INSERT INTO quiz_attempt VALUES (999001, 'lrn-00001', 1, 'c01', 0, 1, '2026-10-05T00:00:00Z')")
    conn.execute("INSERT INTO quiz_attempt VALUES (999002, 'lrn-00001', 1, 'c01', 0, 1, '2026-10-04T23:59:59Z')")
    ids = {r[0] for r in queries.recent_attempts(conn, "lrn-00001", "c01", "2026-10-05")}
    assert 999001 in ids and 999002 not in ids
