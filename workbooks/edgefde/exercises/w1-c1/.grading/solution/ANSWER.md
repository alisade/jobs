# ANSWER: edgefde/w1-c1 Idempotent vibration-feature ingest

## Approach

Started with the contract, because everything downstream depends on the key: a Pydantic v2 model with
`extra="ignore"`, UTC normalisation and finite checks. Then the store (one transaction, upsert with a
seq guard), the consumer (commit after write), DQ, and the backfill that reuses the same parse and
write path. Tested crash points by throwing the consumer away between poll and write.

## Fix

Delivery is at-least-once: offsets are committed only after the SQLite transaction commits, and never
when the write fails, so anything not durably stored is redelivered. Duplicates are harmless because
the write is an upsert keyed by (device_id, window_start) that only replaces a row when the incoming
seq is higher. Together that is effectively once for the feature table. It relies on the gateway
producing a stable window_start and a monotonic seq per device; if either breaks, the key breaks.
Quarantine rows are written in the same transaction and are unique by source, so bad messages never
block a partition and are stored once. The backfill validates the whole day and runs DQ before
opening the transaction; 2026-10-15 fails on pump-03 completeness (about 80%) and writes nothing.

## Trade-offs / what I would do in production

confluent-kafka with `enable.auto.commit=false`, synchronous commit after the DB commit, and an
`on_revoke` handler so a rebalance does not commit a half-processed batch. Schema registry with BACKWARD
compatibility instead of a hand-written version field. Timescale or partitioned Parquet/Iceberg
instead of SQLite. Backfills as orchestrator partitions (Dagster or Airflow) so reruns are visible.
Alert on quarantine rate per device and on any DQ failure; a silent quarantine is still data loss.
