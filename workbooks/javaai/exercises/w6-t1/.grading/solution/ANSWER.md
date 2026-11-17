# ANSWER: javaai/w6-t1 The Recent activity card got slow

## Approach

Started from the PostgreSQL plan: Index Scan Backward on idx_attempt_created_learner with a Filter
and 40,981,233 rows removed to return 11. Query Insights agrees: 2.95M rows examined per call on
average. Reproduced locally with make explain: SCAN a USING INDEX idx_attempt_created_learner, 6.9 ms
on 200k rows.

## Root cause

No index matches the query. The existing (created_at, learner_id) index leads with the range column,
and date(created_at) wraps the column so even that range is unusable. The planner walks the index
backwards for ORDER BY ... LIMIT and filters every row, so time grows with the table: 290 ms at 8M rows
in July, 1.8 s at 41M. VACUUM ANALYZE ran at 10:20 with no change: statistics do not matter when the
only plan reads everything; more buffers would only cache the scan.

## Fix

V7 adds (learner_id, course_id, created_at). The predicate becomes created_at >= ?, equivalent for ISO
8601 text because a day string sorts before every timestamp of that day. Plan after: SEARCH a USING
INDEX idx_attempt_learner_course_created (learner_id=? AND course_id=? AND created_at>?), 0.01 ms; no
temp sort. Results equal the old semantics including the boundary day. 9/9 tests.

## Trade-offs / what I would do in production

CREATE INDEX CONCURRENTLY in its own migration. Another index on a hot table costs writes: check
whether the export still needs PERF-88's index. Partition attempts by month. Alert on rows examined
per row returned.
