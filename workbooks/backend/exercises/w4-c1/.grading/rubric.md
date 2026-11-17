# Rubric: backend/w4-c1 Opportunity stage transitions with an outbox (Fastify + Kysely)
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Transaction and concurrency design | 15 | Full: one withTenant transaction; FOR UPDATE before the checks; version compared and also guarded in the UPDATE; history and outbox inside the transaction; no awaits on external systems inside it. Partial: correct but outbox or history written after commit, or no lock. |
| 3 | Error contract | 10 | Full: consistent RFC 9457 bodies from a central error handler, stable `type` URIs, useful extension members, 500s without internals, 404 for other tenants (no existence leak). Partial: correct codes, inconsistent bodies. |
| 4 | Graceful shutdown | 10 | Full: readiness flips first, new work refused with 503 and Connection: close, in-flight tracked and drained, app.close() then exit, a timeout path with exit(1); ANSWER relates it to preStop and terminationGracePeriodSeconds. Partial: app.close() only. |
| 5 | Code quality and types | 5 | Small functions, Kysely types used, no `any` leaks in the handler, Zod schema strict. |
| 6 | ANSWER.md trade-offs | 10 | Explains the dual-write problem the outbox solves; pessimistic vs optimistic locking and why both here; agent retries (expected_version makes a retry a 409, so an Idempotency-Key or returning the existing result for a replay is the next step); per-aggregate event ordering in the relay. |
Total: 100
