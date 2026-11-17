# Reference: javaai/w6-t1

## Root cause

The query filters `learner_id = ? AND course_id = ?` and a date range, ordered by `created_at DESC`.
The only index on quiz_attempt is PERF-88's `(created_at, learner_id)`, built for the nightly export.
It leads with the range column, and the query wraps the column in `date(...)`, so no index can serve
the range at all. The planner picks the cheapest thing it has: walk that index backwards to satisfy
ORDER BY ... LIMIT 20 and filter every row. For a learner with 11 rows in the window it reads all 41M
index entries: cost proportional to the table, 290 ms at 8M rows in July, 1.8 s now.

## Not vacuum

The plan reads the whole index whatever the statistics; VACUUM ANALYZE did not change it (it ran at
10:20 with p95 unchanged). More shared_buffers would cache the scan, not avoid it.

## Fix (`.grading/solution/`)

- `migrations/V7__attempt_learner_course_created.sql`: `(learner_id, course_id, created_at)`. Equality
  columns first, range last: the index finds the learner+course slice, starts at the date, and is already
  in created_at order, so no sort.
- `queries.py`: `created_at >= ?` instead of `date(created_at) >= ?`. Equivalent because the column is
  ISO 8601 UTC text and 'YYYY-MM-DD' sorts before any timestamp on that day. In PostgreSQL with a
  timestamptz column: `created_at >= $3::date`.

Plan after: `SEARCH a USING INDEX idx_attempt_learner_course_created (learner_id=? AND course_id=? AND created_at>?)`.

## Follow-ups

`CREATE INDEX CONCURRENTLY`; an index on a 41M-row insert-heavy table costs writes, so check whether
PERF-88's index is still needed; partition quiz_attempt by month; alert on rows examined / returned.
