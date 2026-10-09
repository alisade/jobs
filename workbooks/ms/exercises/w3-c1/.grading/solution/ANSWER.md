# ANSWER: ms/w3-c1

## Approach
Health from the Delta log (active files only), per partition when the table is partitioned. A table or
partition breaches when it has at least min_files files and the small-file ratio is at or above the threshold.
Breaching partitions are rewritten with partition filters; Z-order when configured, bin-compaction otherwise.
VACUUM is guarded: minimum retention is max(7 days, the table's deletedFileRetentionDuration), checked before
any rewrite, with an explicit override flag.

## Fix
Implemented health, planning, guarded vacuum, per-table maintenance and the job loop with error isolation.
Tested partitioned tables, dry run side effects, idempotency, the table-property retention and the CLI exit code.

## Trade-offs / what I would do in production
Schedule after the heavy loads to keep CU spikes predictable; in Fabric add V-Order to the OPTIMIZE for tables
read by Direct Lake or the SQL endpoint, and enable optimized write. Keep 7+ days of retention for time travel and
long readers; storage is cheap compared with a broken audit. Alert on status=failed and trend num_files per table.
