# ANSWER: edgefde/w1-c1 Idempotent vibration-feature ingest

## Approach

<!-- How you structured the contract, store, consumer and backfill, and the order you built them in. -->

## Fix

<!-- What you implemented. One paragraph on delivery semantics: at-least-once delivery plus what makes
the result effectively once, and exactly where the offset commit sits relative to the write. -->

## Trade-offs / what I would do in production

<!-- Real Kafka (confluent-kafka: enable.auto.commit=false, commit after write, rebalance callbacks),
a schema registry, Postgres/Timescale or Parquet instead of SQLite, backfill orchestration (Airflow or
Dagster partitions), alerting on quarantine rate and DQ failures. Short. -->
