# Rubric: javaai/w6-t1 The dashboard's Recent activity card got slow as data grew
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (several rows are regression guards) |
| 2 | Root cause identified | 25 | Full: no index matches the predicate. The only candidate, (created_at, learner_id) from PERF-88, leads with the range column; and `date(created_at)` wraps the column so no index can use the range at all. The planner walks that index backwards for the ORDER BY and filters every row (Rows Removed by Filter 41M), so cost grows linearly with table size: 290 ms at 8M rows, 1.8 s at 41M. Partial (10-15): "missing index" without the column-order and function-on-column reasons, or without the growth explanation. Zero: vacuum, buffers. |
| 3 | Evidence | 20 | Quotes the plan (Index Scan Backward with Filter, rows removed, buffers), Query Insights rows examined vs returned, the July baseline, and the local plan and timing before and after. |
| 4 | Red herring handled | 10 | VACUUM ANALYZE ran with no change; statistics and bloat do not matter when the plan reads the whole index; more buffers would cache a full scan, not avoid it. |
| 5 | Fix quality | 10 | V7 index (learner_id, course_id, created_at): equality columns first, range last, so it also provides the order; predicate rewritten to `created_at >= ?` with an argument why it is equivalent for ISO timestamps; V1-V6 untouched. |
| 6 | Production follow-ups | 5 | CREATE INDEX CONCURRENTLY, write cost of the extra index, keep or drop PERF-88's index based on the export, monthly partitioning of attempts, plan checks in CI or pg_stat_statements alerts. |
Total: 100
