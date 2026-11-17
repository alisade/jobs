# ANSWER: backend/w5-c1 Idempotent timeline consumer in Go

## Approach

<!-- How you made Apply idempotent, where the dedupe record lives and why it must be in the same
transaction, how you ordered apply and commit, how retries and the DLQ work, how shutdown works. -->

## Fix

<!-- What you changed in consumer/consumer.go and how you verified it (make test, make replay). -->

## Trade-offs / what I would do in production

<!-- Short. E.g. processed-event table retention and size, natural idempotency vs a dedupe table,
DLQ replay tooling and alerting, per-partition concurrency vs ordering, commit batching,
consumer lag metrics, rebalances. -->
