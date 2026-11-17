# ANSWER: backend/w4-c1 Opportunity stage transitions with an outbox (Fastify + Kysely)

## Approach

<!-- How you structured the transaction, validation and errors; what you tested first. -->

## Fix

<!-- What you changed and why: the transaction boundary, FOR UPDATE plus the version check, the outbox
row, problem details, graceful shutdown. How you verified it. -->

## Trade-offs / what I would do in production

<!-- Short. Pessimistic lock vs optimistic version (and why both), what an agent retry does here
(idempotency keys?), outbox relay and event ordering per aggregate, shutdown timing vs
terminationGracePeriodSeconds and preStop, OpenAPI for the contract. -->
