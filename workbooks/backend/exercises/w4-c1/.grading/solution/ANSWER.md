# ANSWER: backend/w4-c1 Opportunity stage transitions with an outbox (Fastify + Kysely)

## Approach

Started from the contract: Zod schema and the problem+json error handler, then the transaction, then
shutdown. Ran the visible tests after each step and wrote down the concurrency and rollback cases
before coding them.

## Fix

- `transitions.ts`: strict Zod body; tenant header required; one `withTenant` transaction that does
  `SELECT ... FOR UPDATE`, compares `expected_version` (409 with current_version), checks `ALLOWED`
  (422) and the closed-won rules (422), updates with `WHERE version = old`, inserts `stage_history` and
  the `outbox` row with the full payload, and returns the result from inside the transaction.
- `app.ts`: central error handler mapping `ProblemError`, Fastify 4xx and unknown errors to RFC 9457;
  404 handler; readiness reflects draining.
- `shutdown.ts`: SIGTERM flips `draining`, refuses new requests with a 503 problem, waits for in-flight
  requests (counted in onRequest/onResponse), closes the app, exits 0 (1 on timeout).

## Trade-offs / what I would do in production

- Outbox in the same transaction avoids the dual write; publishing is at least once, so consumers dedupe
  on event_id and check version.
- FOR UPDATE plus the version check: the lock prevents interleaving on a real pool, the version tells a
  client its view is stale.
- An agent retry after a timeout gets a 409 because the version moved; an Idempotency-Key that replays the
  first response is the clean fix.
- timeoutMs below terminationGracePeriodSeconds, plus a short preStop sleep.
