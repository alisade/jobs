# Rubric: backend/w3-c1 Idempotency keys that survive concurrent retries
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Atomic claim design | 20 | Full: the unique constraint arbitrates (INSERT first, IntegrityError or ON CONFLICT path), no check-then-insert or in-process lock (an asyncio.Lock would not work across pods); claim, complete and release are short separate transactions or one atomic phase. Partial: works in tests through a process-local lock or a retry loop without a constraint. Zero: still racy. |
| 3 | Semantics | 10 | Fingerprint over method, path and canonical body; 422 vs 409 vs replay distinguished correctly; Retry-After; stored 4xx replayed, 5xx and exceptions release the key; per-tenant scoping; expiry replaces the row. |
| 4 | Errors and code quality | 10 | RFC 9457 bodies with stable type URIs, readable code, no swallowed exceptions, bounded loops. |
| 5 | ANSWER.md trade-offs | 10 | Full: names the crash-between-handler-and-completion gap and a remedy (lease or same-transaction completion), Postgres ON CONFLICT, retention/cleanup, key derivation for workflow activities and agents. Partial: generic. |
Total: 100
