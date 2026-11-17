# ANSWER: backend/w5-c1 Idempotent timeline consumer in Go

## Approach

The topic and relay are at-least-once, so every record can arrive twice and old records can arrive
after newer ones. I made the consumer effectively-once with two independent guards inside one
transaction: a processed-event row keyed by event_id, and a version check per activity. The offset
is committed only after the record is handled, so a crash causes a redelivery, never a loss.

## Fix

- `Apply`: skip if processed; mark processed; skip if the stored version is >= the event version;
  never resurrect a tombstone; adjust the counter by live-after minus live-before.
- `HandleRecord`: poison -> DLQ now; store errors retried with linear backoff, 3 attempts, then DLQ
  with attempts and reason; nil means "safe to commit".
- `RunPartition`: stop taking work once ctx is cancelled; handle and commit under
  `context.WithoutCancel` so the in-flight record finishes; a failed commit returns an error.
Verified with `make test` (-race) and `make replay` (count 1, final subject, one DLQ message).

## Trade-offs / what I would do in production

- Processed-event table: in Postgres, `processed_events(event_id primary key, processed_at)` written
  in the same transaction, with a retention job longer than topic retention plus replay window.
- DLQ: alert on any message, store reason and attempts, provide a replay command after a fix.
- Metrics: consumer lag per partition, DLQ rate, apply latency; readiness that reflects lag.
- Rebalances: on partition revoke, finish the in-flight record and commit before releasing.
