# Rubric: backend/x-2 The migration that took the API down
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: the reporting session idle in transaction since 01:40 held AccessShareLock on activities; 0057's first statement (ADD COLUMN) requested AccessExclusiveLock and waited; with no lock_timeout it waited indefinitely; every later API lock request queued behind the waiting AccessExclusive request (lock queue), so reads and writes stalled while the database was idle; the single-transaction migration would also have held AccessExclusive through the FK scan and plain index build. Partial: "locks" or "long migration" without the queue mechanism or without the idle-in-transaction holder. Zero: blames pool size, CPU or the FK scan time alone. |
| 3 | Evidence | 20 | Full: pg_blocking_pids chain (48213 blocked by 47102; app pids blocked by 48213), the granted=f AccessExclusiveLock row, idle in transaction since 01:40, lock_timeout = 0 and idle_in_transaction_session_timeout = 0, metrics showing idle CPU with 238 sessions waiting, recovery seconds after the kill. Partial: two of these. |
| 4 | Red herring | 5 | Explains why raising the pool and restarting pods could not help (more waiters in the same queue) and why staging was fast. |
| 5 | Migration rewrite | 10 | lock_timeout and statement_timeout; FK NOT VALID then VALIDATE in a later migration (ShareUpdateExclusive); CREATE INDEX CONCURRENTLY in a no-transaction file with a note on INVALID index cleanup; baseline untouched; linter not weakened. |
| 6 | Prevention | 5 | Lint in CI, retries with backoff on lock_timeout, idle_in_transaction_session_timeout and statement_timeout for the reporting role or a replica for it, alerts on lock waits and old transactions, pre-flight check for long transactions. |
Total: 100
