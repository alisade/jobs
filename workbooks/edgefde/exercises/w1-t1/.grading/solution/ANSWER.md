# ANSWER: edgefde/w1-t1 Gaps in window counts after every consumer restart

## Approach

Started from `summary.txt` (8640 produced, 8240 stored: 400 windows missing, every pump short
somewhere) and lined up each supervisor restart in `sink.log` with the auto-commit line just before it.

## Root cause

The consumer runs with `enable_auto_commit=True`, which commits the previous poll's positions at the
start of every poll, while the sink keeps records in an in-memory buffer and writes them only every
5 polls. Committed offsets are therefore up to four polls ahead of SQLite. A restart throws the
buffer away and the new consumer resumes from the committed offsets, so those records are never
redelivered.

Evidence (`incident/sink.log`):

```text
broker: auto-commit group=dashboard-sink offsets={0: 2720, 1: 0, 2: 2720} sum=5440
supervisor: sink process restarted: deploy sink:2026.10.20-1 (rows in dashboard table: 5200)
...
broker: auto-commit group=dashboard-sink offsets={0: 5520, 1: 0, 2: 2880} sum=8400
supervisor: sink process restarted: OOMKilled (exit 137) (rows in dashboard table: 8000)
```

240 lost at the deploy, 160 more at the last OOM: 400, matching `summary.txt`. The first OOM lost
nothing (2800 committed, 2800 stored) because it landed right after a flush.

The holes sit at different event hours because pumps 01/02/05/06 hash to partition 0 and pumps 03/04
to partition 2; round-robin polling leaves partition 0 further behind in event time, so the same
restart drops 10:00-11:00 windows for partition 0 devices and 21:00-22:00 for partition 2.

Ruled out: the under-replicated `vibration.features-1` recovered at 06:04 and partition 1 has no
devices at all; the lag warnings mean the sink was behind, which explains why lost event hours trail
the restart times, but lag does not lose data.

## Fix

Auto-commit off; commit immediately after `write_rows` returns. Primary key plus upsert on
`(device_id, window_start)` so a kill between write and commit only redelivers rows that overwrite
themselves. Verified with `make run` (8640 distinct / 8640 rows) and by killing after and before
writes; batching unchanged (about 22 transactions for the day).

## Trade-offs / what I would do in production

Recover the day by resetting the group's offsets to 2026-10-20T00:00Z (or backfilling from the
archive), which is safe now that the write is idempotent. In confluent-kafka: `enable.auto.commit=false`,
synchronous commit after the DB commit, and a revoke callback that flushes or drops the buffer before
partitions move. Add a produced-vs-stored check per device-hour with an alert.
