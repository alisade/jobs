# Reference: edgefde/w1-c1

The reference implementation is in `.grading/solution/ingest/`.

Key points:

- `models.py`: Pydantic v2 model with `extra="ignore"` (forward compatible), a field validator that
  rejects naive datetimes and converts to UTC, finite checks on floats (JSON `NaN`/`Infinity` parse to
  floats in Python, so they must be rejected explicitly), and a `key` property used everywhere.
  `parse_record` maps `json` and `ValidationError` to `InvalidRecord("<loc>: <msg>")`.
- `store.py`: `BEGIN IMMEDIATE ... COMMIT` around one `executemany` upsert plus the quarantine
  inserts. The upsert is `ON CONFLICT (device_id, window_start) DO UPDATE ... WHERE excluded.seq >
  features.seq`, so replaying an old reading is a no-op. Quarantine has `UNIQUE (source)` with
  `INSERT OR IGNORE`.
- `consumer.py`: poll, parse, `write_batch`, then `commit()`. No try/except around the write: if it
  fails, the exception propagates, offsets stay where they were, and the restarted consumer re-reads
  from the last commit. At-least-once delivery plus an idempotent write keyed on a natural id is
  "effectively once"; Kafka transactions would not make the SQLite side idempotent.
- `dq.py`: counts distinct keys per device (duplicates do not inflate completeness), flags records
  outside the partition, unknown devices and the RMS outlier rate.
- `backfill.py`: reads and validates the whole day first, runs DQ, raises before writing, then one
  transaction. Running it twice, or after live ingest, changes nothing.

Production mapping: confluent-kafka with `enable.auto.commit=false`, `consumer.commit(asynchronous=False)`
after the DB commit, an `on_revoke` callback that finishes or abandons the in-flight batch, a schema
registry with BACKWARD compatibility, Timescale/Postgres or partitioned Parquet/Iceberg for the store,
backfills as Dagster/Airflow partitions, and alerts on quarantine rate and DQ failures.
