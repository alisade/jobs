# Reference: backend/w5-c1 Idempotent timeline consumer in Go

Solution: `.grading/solution/consumer/consumer.go`.

## Apply
1. `if tx.Processed(ev.EventID) { return nil }`, then `tx.MarkProcessed(ev.EventID)` in the same
   transaction. If the dedupe row were written in a separate transaction, a crash between the two
   either loses the event (marked, not applied) or applies it twice (applied, not marked).
2. Version guard: `if exists && cur.Version >= ev.Version { return nil }`. This covers duplicates
   with a new event id, stale edits from a producer retry, and a late edit after a delete (the
   tombstone carries the delete's version). A Logged or Edited event on a tombstone is also ignored.
3. Counter: compute `live(before)` and `live(after)` and add the difference. Incrementing on
   "Logged" and decrementing on "Deleted" is wrong once events can be duplicated or reordered.

## Delivery
- `RunPartition`: poll, handle, then commit `offset+1`. Commit-before-apply turns any apply failure or
  crash into a lost event; apply-before-commit turns it into a redelivery, which Apply absorbs.
- `HandleRecord`: poison -> DLQ immediately (retrying cannot help); store error -> retry with backoff,
  3 attempts total, then DLQ with attempts and the last error. Returning nil lets the loop commit, so
  one bad message never stalls the partition.
- Shutdown: check `ctx.Err()` before polling; run the handler and commit under
  `context.WithoutCancel(ctx)` so SIGTERM does not abort a half-done record. Kubernetes gives the
  pod `terminationGracePeriodSeconds` to do this.

## Interview angles
- "Exactly once?" Kafka transactions give exactly-once between Kafka topics; with an external
  database the practical answer is at-least-once delivery plus an idempotent consumer.
- Processed-event table growth: keep ids for longer than the maximum redelivery window (retention
  of the topic plus replay window), partition or TTL the table, or rely on natural idempotency (the
  version guard alone makes this consumer correct except for exact-duplicate counters).
- Ordering vs throughput: one goroutine per partition keeps per-account order; more parallelism
  needs per-key queues inside a partition and careful offset tracking (commit the lowest unfinished).
- DLQ is a product: alert on it, show the reason, give an operator a replay command.
