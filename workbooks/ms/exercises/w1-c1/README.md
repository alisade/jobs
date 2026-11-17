# ms/w1-c1: Medallion incremental load with watermark, MERGE and SCD2

Type: coding. Estimate: 2-3 h. Exam: DP-700 - Ingest and transform data (30-35%): design and implement loading patterns (full and incremental loads, dimensional model prep, duplicate, missing and late-arriving data).

## Scenario

Northwind Logistics lands shipment tracking events from three carrier APIs into the bronze area of a
Fabric lakehouse (`Files/bronze/shipments/*.parquet`) every 15 minutes. The landing pipeline stamps every
row with `_ingested_at` (copy time) and `_ingest_seq` (increasing per landing run). Carriers resend events,
send them out of order, and the copy sometimes lands a file late with an `_ingested_at` that is already
older than the last processed watermark.

The current notebook does a full overwrite of silver every run. It now takes 40 minutes, burns CUs on
the F64 capacity, and the BI team complained that a resent "PICKED" event overwrote a "DELIVERED" status.
Operations also wants a routing history dimension (`dim_shipment`) so they can answer "which carrier
and destination did shipment X have at time T" for SLA disputes.

You are rewriting the notebook as an incremental load. Locally it is a Python module that uses polars and
deltalake (delta-rs) instead of PySpark (no JVM on this machine), but the Delta tables, MERGE semantics,
versions and time travel are the same Delta protocol a Fabric lakehouse uses.

## Your task

Implement every TODO in `src/medallion.py`:

1. **Watermark control table** (`read_watermark`, `write_watermark`): a Delta table at `control_path`
   with `source`, `watermark`, `updated_at`. Upsert by source; never move a watermark backwards; no commit
   when the value does not change.
2. **Incremental bronze read** (`validate_schema`, `read_bronze_increment`): read all parquet files,
   validate each against `BRONZE_SCHEMA` (raise `SchemaError` on missing columns or wrong types), and return
   rows with `_ingested_at > watermark - lookback`. The lookback re-reads a safety window so late-landed
   files are not lost; everything downstream must therefore be idempotent.
3. **Quality and dedupe** (`reject_invalid`, `dedupe_latest`): drop rows with a null `shipment_id` or
   `event_ts`; keep one row per shipment: latest `event_ts`, ties broken by highest `_ingest_seq`.
4. **Silver MERGE** (`merge_silver`): create on first write, then MERGE on `shipment_id`. Update a matched row
   only when the incoming row is newer (later `event_ts`, or same `event_ts` and higher `_ingest_seq`).
   A late, older event must never overwrite a newer status. No write for an empty frame.
5. **SCD type 2 dimension** (`apply_scd2`) over `DIM_TRACKED = [carrier, destination]`:
   - one row per version with `version` (1, 2, ...), `effective_from` (= event_ts of the change),
     `effective_to` (null while current), `is_current` (exactly one current row per shipment);
   - apply ALL valid changes of the batch (not the deduplicated frame) per shipment in
     `event_ts`, `_ingest_seq` order, so three changes in one batch give three versions;
   - no new version when the tracked attributes are unchanged (status-only changes do not version);
     comparison is null-safe (null == null is "unchanged");
   - rows with `event_ts <= effective_from` of the open version are replays or late history and are
     ignored for the dimension (documented simplification: no back-dated version insertion);
   - when a new version opens, close the previous one: `effective_to` = new `effective_from`;
   - no commit at all when nothing changed.
6. **Orchestration** (`run_batch`): read -> reject -> dedupe -> merge silver -> SCD2 -> commit watermark
   (= max of old watermark and max `_ingested_at` read) last, and only when rows were read. A
   `SchemaError` must leave silver and the watermark untouched. Return a `BatchResult`.

## Acceptance criteria

- `make test` passes (happy path).
- Re-running a batch inside the lookback adds no rows, no dimension versions, and no dimension commit.
- An empty increment creates no new Delta versions in any table.
- Late-landed files inside the lookback are picked up; the watermark never moves backwards.
- A late, older event never overwrites a newer silver row.
- Multiple changes for one shipment in one batch produce ordered SCD2 versions with correct effective ranges.
- Null keys / null event times are rejected and counted; null tracked attributes compare null-safely.
- Schema drift (missing column or changed type) raises `SchemaError` before anything is written.
- Silver history shows a MERGE operation and time travel to version 0 returns the first load.

## How to run

```
make setup     # uv sync: creates .venv with polars, deltalake, pytest
make test      # visible tests
make clean
```

Then from the workbooks root: `/grade ms/w1-c1`.

## What to submit

`src/medallion.py` and a filled `ANSWER.md`.

## How this maps to Fabric

| Local | Fabric notebook |
|---|---|
| `pl.read_parquet` over `Files/bronze/...` | `spark.read.parquet("Files/bronze/shipments")` on the default lakehouse |
| `write_delta(mode="merge")...when_matched_update_all(predicate=...)` | `MERGE INTO silver_shipments t USING src s ON ... WHEN MATCHED AND s.event_ts > t.event_ts THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *` or `DeltaTable.forName(...).merge(...)` |
| `DeltaTable(path).history()` / `read_delta(version=0)` | `DESCRIBE HISTORY silver_shipments` / `SELECT ... VERSION AS OF 0` |
| control Delta table | the same pattern, or a warehouse control table read by a pipeline Lookup |
| run_batch parameters | notebook parameter cell, passed from a pipeline Notebook activity (`notebookutils.notebook.exit` to return metrics) |

Things delta-rs does not do that Fabric does: V-Order (a Fabric write-time parquet optimization; disabled by
default in new workspaces, enabled per session, table property or `OPTIMIZE ... VORDER`), optimized write, and the
Spark SQL `MERGE INTO` syntax. The table protocol, the
transaction log and the MERGE semantics are the same.

## Study guide links

- [Week 1 Tue - Spark notebooks and Delta tables](../../../../microsoft-adf-powerapps-study-plan.html#week1)
- [Week 1 Weekend - Loading patterns lab](../../../../microsoft-adf-powerapps-study-plan.html#week1)
- [Module: Work with Delta Lake tables in Fabric](https://learn.microsoft.com/en-us/training/modules/work-delta-lake-tables-fabric/)
- [Module: Organize a Fabric lakehouse using medallion architecture](https://learn.microsoft.com/en-us/training/modules/describe-medallion-architecture/)
- [Lakehouse and Delta tables (V-Order)](https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order)
- [NotebookUtils](https://learn.microsoft.com/en-us/fabric/data-engineering/notebook-utilities)
