# Rubric: backend/w2-t1 The account timeline got slow after release 2026.44
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (two visible tests are guards that already pass) |
| 2 | Root cause | 30 | Full: the 2026.44 change cast the indexed column (`account_id::text = $2`) to dodge the kdb 4.0 text-parameter error; a function or cast on the column makes the predicate unusable as an index condition, so the plan reads the whole tenant via the tenant prefix, filters account_id and sorts. Partial: "missing or wrong index" or "bad plan" without naming the cast. Zero: statistics, capacity or data growth. |
| 3 | Evidence | 20 | Quotes the Filter vs Index Cond lines and buffer counts from explain-2026.43/44 (or make explain), the diff hunk, and pg_stat_statements mean/buffers; ties the canary timing to the release. |
| 4 | Ruling out the red herrings | 10 | Explains why ANALYZE could not help (the predicate is not sargable whatever the stats), why HPA scaling did not (time is in the DB span, CPU follows buffer reads), and why the weekend import is not the step change. |
| 5 | Fix and prevention | 10 | Casts the parameter (`$2::uuid`) not the column, verified with a plan; prevention: plan regression checks in CI or staging (auto_explain, buffer budgets), pg_stat_statements per-queryid alerts after deploys, typed parameters in kdb. |
Total: 100
