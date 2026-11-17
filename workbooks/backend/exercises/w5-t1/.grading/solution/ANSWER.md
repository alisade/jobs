# ANSWER: backend/w5-t1 Duplicate stage-change events after the relay restart

## Approach

Lined up relay-a.log and relay-b.log by outbox id, then compared the `message_event_id` in the relay
logs and the `event_id` in consumer.log with the `event_id` column in outbox-dump.csv, then replayed
with `make repro` and read `outbox/relay.py`.

## Root cause

The relay stamps every message with a fresh `uuid.uuid4()` as `event_id` at publish time instead of
the outbox row's `event_id`, so the same outbox row published twice arrives as two different events and
the consumer's dedupe (correct, keyed on `event_id`) cannot recognize it.

Evidence:
- outbox-dump.csv: row 18201 has `event_id` from the outbox, but relay-a.log and relay-b.log show
  different `message_event_id` values for `outbox_id=18201`, and neither matches the dump.
- consumer.log: the same `opp`/`version` applied twice with two different event ids, and
  `skipped_duplicates=0` over the window with `received=712 applied=712`.
- make repro (starter): `outbox rows=500 published=712 consumer applied=712 skipped_duplicates=0
  duplicated stage changes=212`.

The trigger is ordinary at-least-once behavior: relay-a claimed a 500-row batch, published 212 rows
slowly (produce p99 1.8 s while broker-2 restarted), got SIGTERM and was killed after the 30 s grace
period before it reached its single "mark sent" at the end of the batch. relay-b claimed the same 500
rows when the lease expired (relay-b.log: "lease expired, previous owner relay-a") and published them
all, so 212 rows went out twice. That redelivery is expected and is exactly what consumer dedupe is for;
it only became visible because the identity was regenerated. Two smaller defects widened it: rows are
marked sent only after the whole batch (so a crash republishes the whole published prefix), and the
claim is a SELECT then an unconditional UPDATE (a race lets two replicas claim the same rows, and a
relay never checks it still owns rows before publishing).

The broker restart and latency spike are a contributing trigger (slow batch, grace period exceeded),
not the cause: they cannot change message ids.

## Fix

`outbox/relay.py`:
- message header `event_id` = the outbox row's `event_id`;
- claim is one `UPDATE ... WHERE id IN (SELECT ... pending OR lease expired ... LIMIT n) RETURNING *`;
- per row: check the claim is still ours and unexpired, publish, `UPDATE ... SET status='sent' WHERE
  id = ? AND claimed_by = ?`; stop the batch if the lease is gone.
Verified: `make repro` now shows `published=500 consumer applied=500 duplicated stage changes=0` (the
simulated kill lands between rows; a kill between publish and mark-sent would republish one row,
which the consumer now skips), and the visible tests pass.

## Trade-offs / what I would do in production

Size batches so a batch finishes well inside the termination grace period (or stop claiming on SIGTERM
and only finish the in-flight row). Keep leases longer than the worst produce latency and renew them.
Make the event-id header part of the event contract and lint it in CI. Consider Debezium's outbox
router, which carries the outbox id as the message key or header. Alert on outbox age and on
"same aggregate version applied twice" in the consumer.
