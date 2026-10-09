# Reference: ms/w3-c1

Reference implementation: `.grading/solution/src/maintenance.py`.

## Design

- **Health** comes from the Delta log, not a directory listing: `get_add_actions()` is the set of files in
  the current version. Tombstoned files still on disk are VACUUM's business, not OPTIMIZE's.
- **Plan** per partition for partitioned tables. Compacting the whole table rewrites healthy partitions,
  burns capacity and invalidates caches for nothing. delta-rs `partition_filters=[("region","=","EU")]`
  is the equivalent of `OPTIMIZE tbl WHERE region = 'EU'`.
- **Z-order** when configured: it co-locates values of the filter column so file skipping works; it also
  bin-packs, so it replaces compaction rather than following it.
- **Retention guard first.** A misconfigured policy should fail the table before it rewrites anything.
  Minimum = max(168 h, `delta.deletedFileRetentionDuration`). Override is an explicit flag, mirroring
  `spark.databricks.delta.retentionDurationCheck.enabled=false`.
- **Idempotent:** a compacted table no longer breaches thresholds, so the second run is a no-op with no
  new Delta version.
- **Error isolation:** one missing or corrupt table becomes an entry in `errors`; the run status is `failed`
  and the CLI exits non-zero so the pipeline's failure path and alert fire.

## Why RETAIN 0 HOURS broke things

VACUUM deletes files no longer referenced by the current version once they are older than the retention.
A reader pinned to an older version (long Spark job, time travel query, a Direct Lake framing that has not
refreshed) still needs them, so it fails with file-not-found; time travel beyond the retention is gone.

## Fabric specifics worth knowing for the exam

- V-Order: Fabric write-time optimization (sorting, row-group distribution, encoding, compression),
  compatible with open Delta/parquet readers. Helps Direct Lake, SQL analytics endpoint and Power BI reads; costs
  some write time (Learn cites about 15% on average). Disabled by default in new workspaces; enable via
  `spark.sql.parquet.vorder.default`, the table property `delta.parquet.vorder.enabled`, the ReadHeavy resource
  profiles, or apply it during `OPTIMIZE tbl [ZORDER BY (...)] VORDER` / the maintenance dialog.
- Maintenance options in the lakehouse: OPTIMIZE (bin-compaction, optional V-Order, Z-order in code),
  VACUUM with retention, and a cleanup of deletion vectors.
- Optimized write and auto compaction reduce small files at write time.

## Interview angles

- How do you pick the target file size for Direct Lake vs Spark workloads?
- What would you alert on from the report, and how would you trend file counts over time?
- When is partitioning the wrong answer to a slow table?
