# Reference: backend/w2-t1

Injected fault: `queries/timeline.sql` compares `account_id::text = $2`. Fix: `account_id = $2::uuid`
(see `.grading/solution/`).

Why it is slow: the composite index is on `(tenant_id, account_id, occurred_at DESC, id DESC)`. An
expression on the column (`account_id::text`) is not the indexed value, so the planner can only use the
leading `tenant_id` (and the row comparison) as the index condition. It reads every activity of the
tenant (40,000 in the sample, 20,000 of them Orbital Freight's), filters by the text comparison, then
top-N sorts to 50. With the parameter cast instead, the predicate is `account_id = '<uuid>'::uuid`, the
index is seeked on both equality columns, rows come out already in timeline order and the scan stops
after 50: 9 buffers instead of 2,314.

Why the change was made: kdb 4.0 declares string parameters as text; `uuid = text` has no operator
(42883). The right fix is to cast the parameter, or have the wrapper send typed parameters.

Red herrings: the 06:13 autovacuum/analyze and the manual ANALYZE (statistics cannot make a non-sargable
predicate sargable); HPA scaling and CPU (a symptom of buffer reads); the weekend import (gradual growth,
not a step at the release); partitioning (premature, would not fix the cast).

Interview angles: "What makes a predicate sargable?" "How would you catch this before prod?" (plan
snapshots for hot queries in CI on seeded data, auto_explain with log_min_duration in staging,
pg_stat_statements diffs per release). "Expression index on account_id::text?" works but doubles index
maintenance to paper over a wrapper bug.
