# ANSWER: backend/w2-t1 The account timeline got slow after release 2026.44

## Approach

Started from the pager and p95.txt: the step change lines up with the 2026.44 rollout (canary at 13:40
already shows it), not with data growth or autovacuum. HPA scaling did not help and the time is in the
DB span, so it is a query plan problem. Compared incident/explain-2026.43.txt and explain-2026.44.txt,
then read release-2026.44.diff and pg_stat_statements.txt. Reproduced locally with `make explain`.

## Root cause

KEY-2291 changed the timeline predicate from `account_id = $2` to `account_id::text = $2`. kdb 4.0
declares string parameters as text, the old predicate failed with `uuid = text`, and the "fix" cast the
column instead of the parameter. A cast on the indexed column makes the predicate non-sargable: the
index on `(tenant_id, account_id, occurred_at DESC, id DESC)` can only be used for `tenant_id`, so the
plan reads every activity of the tenant and filters:

```
Bitmap Index Scan on activities_account_timeline_idx
  Index Cond: ((tenant_id = 'bu-emea'::text) AND (ROW(occurred_at, id) < ...))
Filter: ((account_id)::text = '5ba8660c-...'::text)
Rows Removed by Filter: 20000
Sort Method: top-N heapsort   Buffers: shared hit=2314
```

versus 2026.43: `Index Scan using activities_account_timeline_idx ... Index Cond: (... account_id =
'5ba8...'::uuid ...)`, `Buffers: shared hit=9`, no sort. pg_stat_statements shows the `::text` variant at
1412 ms mean with ~10 billion buffer hits against 3.9 ms for the old form. The bigger the tenant, the
worse it gets, which is why Orbital Freight (bu-emea) is hit hardest.

Not the cause: statistics (ANALYZE at 15:20 changed nothing, and estimates are not the problem: the
predicate cannot use the index whatever the stats say), capacity (CPU follows the extra buffer reads,
HPA did not help, no lock waits), data growth (gradual, the latency step is a release step).

## Fix

`queries/timeline.sql`: `AND account_id = $2::uuid` (cast the parameter to the column type). This works
with kdb 4.0 text parameters and keeps the index condition. `make explain` now shows an Index Scan on
`activities_account_timeline_idx` with `account_id = '...'::uuid` in the Index Cond, no Sort, and about
9 buffers. Paging results are identical to 2026.43.

## Trade-offs / what I would do in production

- Ship the one-line fix forward (keeps KEY-2291); verify p95 and the pg_stat_statements mean.
- CI plan check: run the hot queries against a seeded database and fail on Seq Scan / Filter on the
  key column or a buffer budget regression (auto_explain in staging too).
- Fix kdb: declare parameter types from the target column, or send uuid values typed as uuid.
- Alert on pg_stat_statements mean regressions per queryid after each deploy.
