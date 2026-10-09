# Reference: ms/w1-c1

The reference implementation is `.grading/solution/src/medallion.py`.

## Key decisions

- **Watermark on ingestion time, not event time.** Event time is carrier-controlled and arrives out of
  order; `_ingested_at` is ours. The lookback (`_ingested_at > watermark - lookback`) re-reads a window so a
  file that landed late with an older stamp is still processed. This makes reprocessing normal, so every
  downstream step must be idempotent.
- **Commit order.** Silver MERGE, then dimension, then watermark. A crash in between re-reads the same rows
  next run, which is safe because the steps are idempotent. Advancing the watermark first would lose data.
- **Dedupe:** sort by key, event_ts, _ingest_seq and take the last per key.
- **Guarded MERGE:** `WHEN MATCHED AND (s.event_ts > t.event_ts OR (s.event_ts = t.event_ts AND
  s._ingest_seq > t._ingest_seq)) THEN UPDATE`. Without the guard a resent old PICKED overwrites DELIVERED.
  In Fabric Spark SQL:
  ```sql
  MERGE INTO silver_shipments t USING increment s ON s.shipment_id = t.shipment_id
  WHEN MATCHED AND (s.event_ts > t.event_ts OR (s.event_ts = t.event_ts AND s._ingest_seq > t._ingest_seq))
    THEN UPDATE SET *
  WHEN NOT MATCHED THEN INSERT *
  ```
- **SCD2 over all changes, not the deduplicated frame.** Dedupe would collapse three reroutes into one
  version. Per key: start from the open version, walk the batch in order, skip rows at or before the open
  version's `effective_from` (replays), skip unchanged tracked tuples (null-safe), chain effective ranges.
  Close the previous current row with the first new `effective_from`.
- **No empty commits.** Every Delta commit is a version and a JSON log file; empty commits bloat the log
  and confuse `DESCRIBE HISTORY` based monitoring.

## Alternatives worth discussing

- Dimension via MERGE with the "union of updates and inserts" trick (Spark idiom) instead of an
  overwrite. The overwrite is fine for a small dimension and keeps the code simple; for a large dimension
  use MERGE so only touched files are rewritten.
- Back-dated versions (late row older than the open version) need version splitting; the exercise
  deliberately ignores them. In production either quarantine them or rebuild the key's history.
- Change Data Feed on silver to drive the dimension instead of reprocessing bronze.
- After many small MERGEs: `OPTIMIZE` (with V-Order in Fabric) and `VACUUM`, see w3-c1.

## Interview angles

- Why is the lookback safe only if the MERGE is guarded?
- What happens to the watermark if the notebook fails after the silver MERGE but before the SCD2 write?
- How would you do this with a Copy job or Dataflow Gen2 incremental refresh instead, and when would you?
