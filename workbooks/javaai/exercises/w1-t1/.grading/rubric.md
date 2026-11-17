# Rubric: javaai/w1-t1 The learner dashboard got slow after a "small" release
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (several rows are regression guards) |
| 2 | Root cause identified | 25 | Full: N+1 introduced by 0.9.0 - one query for enrollments, then per enrollment a lazy course load and a lazy lessons load, then one attempts query per lesson (1 + 2C + L statements, 64-157 per request in the logs), each a sequential scan because quiz_attempt has no learner_id index; semester traffic multiplied it into Cloud SQL CPU saturation; connections held longer, so the Hikari pool exhausted. Partial (10-15): "N+1" without tying it to the release, the counts and the missing index. Zero: pool size, Cloud Run scaling, H2 vs PostgreSQL. |
| 3 | Evidence | 20 | Quotes the session metrics (131/64/157 statements vs 1 for an empty learner), the repeated SQL sample, stmt_per_req jumping from 1.8 to ~74 at release, Query Insights calls and seq scan, and a local reproduction with a statement count before and after. |
| 4 | Red herring handled | 10 | Explains the pool exhaustion as a consequence (slow transactions hold connections), and that 12 x 50 = 600 connections against max_connections 100 would move the failure into the database; at most a temporary mitigation after the fix. |
| 5 | Fix quality | 10 | Constant statements via fetch join or DTO projection plus a grouped aggregate (not just @BatchSize, which still scales with data), deterministic ordering, new migration with an index that matches the predicate. |
| 6 | Production follow-ups | 5 | A test that asserts statement counts (Hibernate statistics or a datasource proxy) in CI, Query Insights / pg_stat_statements alert on calls per request, load test before semester start, CONCURRENTLY index creation. |
Total: 100
