# ms/w3-c1: Lakehouse table maintenance job (OPTIMIZE, Z-order, VACUUM guard)

Type: coding. Estimate: 2 h. Exam: DP-700 - Monitor and optimize an analytics solution (30-35%): optimize a lakehouse table; also Implement and manage (30-35%) for scheduling it.

## Scenario

Contoso Fleet streams vehicle telemetry into a Fabric lakehouse in micro-batches. Six months in,
`telemetry_readings` has 180,000 parquet files averaging 40 KB, Direct Lake reports on it fall back to
DirectQuery, and the SQL analytics endpoint takes minutes for queries that used to take seconds. Someone
"fixed" it last quarter by running `VACUUM ... RETAIN 0 HOURS` from a notebook, which broke a long-running
Spark job reading an older version and wiped the time travel the audit team relies on.

You are writing the scheduled maintenance job: it measures every table, compacts only what needs it
(Z-ordering where configured), vacuums with a hard 7-day guard, and writes a JSON report that the platform
team's alerting reads. Locally it is Python with delta-rs (`deltalake`) instead of a Spark notebook.

## Your task

Implement the TODOs in `src/maintenance.py` (`Policy`, `load_config`, `main` and `_add_actions` are given):

1. `table_health(path, small_file_bytes)`: file count, total/avg/min/max bytes, number and ratio of small
   files, Delta version, partition columns, and the same stats per partition for partitioned tables.
2. `plan_actions(name, health, policy)`: OPTIMIZE when `num_files >= min_files` AND
   `small_file_ratio >= small_file_ratio` (per partition for partitioned tables: only breaching partitions are
   rewritten, via delta-rs `partition_filters`). Use Z-order when the table has Z-order columns configured,
   bin-compaction otherwise. Return the reason.
3. `table_min_retention_hours` and `vacuum_table`: VACUUM refuses any retention below 168 hours, or below the
   table's own `delta.deletedFileRetentionDuration` if that is longer, unless `allow_unsafe_retention` is set
   explicitly. Dry run lists the files and deletes nothing.
4. `maintain_table` / `run_maintenance`: retention guard first (fail before any rewrite), health -> plan ->
   optimize (skipped in dry run) -> vacuum -> health after. One broken table is recorded in `errors` and does not
   stop the others; status `failed` if any error. The report must be JSON serializable.

## Acceptance criteria

- Fragmented tables are compacted (Z-ordered when configured) without losing rows; healthy tables and healthy
  partitions are not rewritten (same file paths).
- A second run is a no-op (no new Delta version).
- Dry run reports the plan and vacuum candidates but creates no version and deletes no file.
- Retention below 7 days (or below the table property) raises `RetentionError` unless explicitly overridden;
  the default run keeps today's tombstoned files so time travel to old versions still works.
- The CLI writes the report and exits non-zero when any table failed.

## How to run

```
make setup
make test
make demo      # builds a fragmented demo lakehouse and runs the job in dry-run mode
make clean
```

Then from the workbooks root: `/grade ms/w3-c1`.

## What to submit

`src/maintenance.py` and a filled `ANSWER.md`.

## How this maps to Fabric

| Local (delta-rs) | Fabric |
|---|---|
| `DeltaTable.optimize.compact()` | `OPTIMIZE tbl` (Spark SQL), lakehouse table **Maintenance** dialog, or the Lakehouse Maintenance pipeline activity |
| `optimize.z_order([...])` | `OPTIMIZE tbl ZORDER BY (col)` |
| no equivalent | `OPTIMIZE tbl VORDER` or `OPTIMIZE tbl ZORDER BY (col) VORDER`: V-Order is a Fabric-specific write-time parquet optimization (row-group distribution, encoding, compression) that helps read-heavy engines such as Direct Lake and the SQL analytics endpoint. It is disabled by default in new workspaces (`spark.sql.parquet.vorder.default=false`) and costs roughly 15% write time. delta-rs does not write V-Order. |
| `vacuum(retention_hours=..., enforce_retention_duration=...)` | `VACUUM tbl RETAIN n HOURS`; Fabric portal and API maintenance fail below 7 days unless `spark.databricks.delta.retentionDurationCheck.enabled=false` in the environment |
| JSON report | Monitoring hub `TableMaintenance` entries, or `notebookutils.notebook.exit(json)` back to a pipeline |

In Fabric you would schedule this as a notebook (or the Lakehouse Maintenance activity, preview) in a pipeline,
after the heavy loads, and also consider optimized write and auto compaction to reduce the need for it.

## Study guide links

- [Week 3 Fri - Optimize performance](../../../../microsoft-adf-powerapps-study-plan.html#week3)
- [Delta Lake table optimization and V-Order](https://learn.microsoft.com/en-us/fabric/data-engineering/delta-optimization-and-v-order)
- [Table compaction (OPTIMIZE, VORDER)](https://learn.microsoft.com/en-us/fabric/data-engineering/table-compaction)
- [Delta table maintenance in Fabric](https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-table-maintenance)
- [Cross-workload table maintenance and optimization](https://learn.microsoft.com/en-us/fabric/fundamentals/table-maintenance-optimization)
