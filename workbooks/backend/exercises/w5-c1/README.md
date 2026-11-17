# backend/w5-c1 - Idempotent timeline consumer in Go

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 5 (Wed: idempotent consumers, DLQ, event design; Thu: Go for platform glue)

## Scenario

Keystone, Lumenfold's replacement for its third-party CRM, shows every account's activity
timeline (calls, emails, meetings) and a live activity counter on the account page. accounts-svc
and pipeline-svc write activity changes to their transactional outbox; the outbox relay publishes
them to the `activity` topic keyed by `account_id` (so one account's events stay in order on one
partition). `timeline-consumer` is a small Go service that reads the topic and maintains the
timeline.

The first spike went to staging last week and sales ops (Dana Whitfield) filed three bugs: the
counter on busy accounts is too high after every relay restart, an activity a rep deleted came
back an hour later, and one malformed event from a load test stopped a whole partition for the
night. Everything upstream is at-least-once by design: producers retry with the same `event_id`,
the relay redelivers after a crash, and a consumer restart re-reads from the last committed
offset. The consumer has to be correct anyway.

## What you have

| Path | What it is |
|---|---|
| `eventlog/` | in-memory topic: partitions, keyed appends, consumer-group commits, readers that start at the committed offset (provided, do not change) |
| `store/` | the consumer's database: `Store.Apply(ctx, fn)` is an all-or-nothing transaction; `MemDLQ` is the dead-letter topic (provided) |
| `consumer/event.go` | the event envelope and `Decode` (returns errors wrapping `ErrPoison`) |
| `consumer/consumer.go` | **your code**: `Apply`, `HandleRecord`, `RunPartition` (`Run` is done) |
| `cmd/replay/` | `make replay`: a messy stream (duplicates, stale edit, late edit after delete, poison) and the resulting timeline |
| `consumer/*_test.go` | visible tests and helpers |

## Requirements

1. **Idempotent apply.** Record the event id as processed in the **same transaction** as the
   timeline change (`tx.MarkProcessed`); an event already processed is a no-op.
2. **Versions.** `Version` is the activity's version after the change (Logged = 1). Ignore any event
   whose version is not newer than the stored one. A delete leaves a tombstone that keeps its version,
   and nothing resurrects a tombstone.
3. **Counter.** `AddCount` must keep the account counter equal to the number of non-deleted
   activities, whatever the delivery order or duplication.
4. **Commit after handling.** Commit `offset+1` only after the record was applied, skipped as a
   duplicate, or parked on the DLQ. A failed commit stops `RunPartition` with an error (the pod
   restarts and the record is redelivered).
5. **Retries and DLQ.** A poison message (`ErrPoison`) goes to the DLQ at once. A store error is
   retried with backoff, 3 attempts in total (`MaxAttempts`), then the record goes to the DLQ with
   the attempt count and reason. The partition keeps moving either way.
6. **Shutdown.** When `ctx` is cancelled (SIGTERM during a rollout), finish the in-flight record,
   apply and commit, take no new record, and return `nil` from `Run`.

## Acceptance criteria (what the grader checks)

- `go test -race` passes on the visible and the hidden tests: duplicate deliveries, commit order,
  a crash between apply and commit, stale edits, late edit after delete, poison message, transient
  failures with and without recovery, shutdown with a record in flight, 4 partitions with duplicates.
- No unbounded waits; every hidden test has a deadline.
- `ANSWER.md` explains your dedupe and ordering decisions and what you would add in production.

## How to run

```bash
make setup      # go build ./...
make replay     # watch the consumer on a messy stream
make test       # visible tests with -race
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/w5-c1
make clean
```
