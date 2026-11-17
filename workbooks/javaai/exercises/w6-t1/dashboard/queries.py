"""Learner dashboard queries (Cloud SQL for PostgreSQL in production; SQLite here, same plan shapes)."""

from __future__ import annotations

import sqlite3

RECENT_ATTEMPTS = """
SELECT a.id, a.quiz_item_id, a.correct, a.created_at
  FROM quiz_attempt a
 WHERE a.learner_id = ?
   AND a.course_id = ?
   AND date(a.created_at) >= ?
 ORDER BY a.created_at DESC
 LIMIT 20
"""


def recent_attempts(conn: sqlite3.Connection, learner_id: str, course_id: str, since: str) -> list[tuple]:
    """The dashboard's "recent activity" card: the learner's last 20 attempts in a course since a date
    (since is 'YYYY-MM-DD', inclusive)."""
    return conn.execute(RECENT_ATTEMPTS, (learner_id, course_id, since)).fetchall()


def plan(conn: sqlite3.Connection, sql: str, params: tuple) -> list[str]:
    return [row[-1] for row in conn.execute("EXPLAIN QUERY PLAN " + sql, params)]
