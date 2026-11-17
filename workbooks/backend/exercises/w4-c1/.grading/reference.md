# Reference: backend/w4-c1

Reference files: `.grading/solution/src/{transitions,app,shutdown}.ts`.

- **Transaction boundary.** `withTenant` opens the transaction, sets `ROLE pipeline_app` and
  `app.tenant_id` locally. Everything (lock, checks, update, history, outbox) happens inside it, and the
  handler returns from inside, so any throw rolls back all writes. That is the whole point of the
  transactional outbox: the event row commits if and only if the state change commits; the relay
  publishes later (at least once).
- **Lock and version.** `SELECT ... FOR UPDATE` serializes concurrent writers on the row on a real pool;
  the `expected_version` check turns a lost update into a 409 the client can act on; `WHERE version =`
  in the UPDATE is a belt-and-braces guard if someone removes the lock later.
- **Errors.** A central `setErrorHandler` turns `ProblemError`, Fastify 4xx (bad JSON) and unknown errors
  into problem+json. 404 for other tenants because RLS hides the row; never reveal existence.
- **Shutdown.** Kubernetes keeps sending traffic for a moment after SIGTERM. Readiness goes 503 first,
  new requests are refused (with Connection: close so the client reconnects elsewhere), in-flight requests
  are counted with onRequest/onResponse and drained, then `app.close()` closes the DB pool, then exit.
  Size `timeoutMs` below `terminationGracePeriodSeconds`; a short preStop sleep covers endpoint propagation.

Interview angles: "Why not publish to Kafka in the handler after commit?" (crash between commit and
publish loses the event; publish before commit emits events for rolled-back changes). "What does an
agent retry do?" (the second call gets 409 because the version moved; with an Idempotency-Key the
service can return the first result instead). "How are events ordered?" (key by aggregate_id, relay in
created_at order per aggregate, consumers check version).
