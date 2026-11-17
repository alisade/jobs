# ANSWER: ms/w1-c1

## Approach
Watermark on `_ingested_at` kept in a Delta control table, read with a lookback window so late-landed files
are picked up. Rows with null keys or event time are rejected. Dedupe keeps the latest event per shipment
(event_ts then _ingest_seq). Silver uses a guarded Delta MERGE so an older event can never overwrite a newer
one. The SCD2 dimension walks every valid change per shipment in event order with a null-safe comparison of
the tracked columns and skips replays at or before the open version. Watermark is committed last.

## Fix
Implemented all TODOs in `src/medallion.py`; added tests for reruns, late files, same-batch multi-change,
nulls, schema drift and time travel.

## Trade-offs / what I would do in production
The lookback costs a re-read of a window each run; size it from observed landing delays. Back-dated SCD2
changes are ignored here; production would quarantine or rebuild that key. Run OPTIMIZE with V-Order and
VACUUM on a schedule because frequent MERGEs create small files. In Fabric this is a parameterized notebook
called by a pipeline Notebook activity with a failure branch and an alert.
