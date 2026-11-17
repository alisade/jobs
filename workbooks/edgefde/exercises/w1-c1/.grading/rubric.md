# Rubric: edgefde/w1-c1 Idempotent vibration-feature ingest with a safe backfill
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Delivery semantics | 15 | Full: commit strictly after the transaction commits, no commit on failure, explains at-least-once + idempotent upsert = effectively once and that it relies on a stable natural key and monotonic seq. Partial: correct code, vague explanation. Zero: commits before write or auto-commit. |
| 3 | Store design | 10 | Full: single transaction per batch (features and quarantine together), ON CONFLICT upsert with a seq guard, quarantine unique by source, WAL or equivalent. Partial: idempotent but not atomic, or seq ignored. |
| 4 | Contract and data quality | 10 | Full: contract rejects with readable reasons, tolerates unknown fields (forward compatibility), DQ counts distinct windows and fails before writing. Partial: checks present but duplicates inflate completeness or DQ runs after the write. |
| 5 | Code quality | 5 | Typed, small functions, no swallowed exceptions, logging instead of prints in library code. |
| 6 | Production notes | 10 | ANSWER.md maps the fake to confluent-kafka settings (enable.auto.commit=false, commit after write, rebalance handling), names the real store and orchestrator choices, and says how quarantine rate and DQ failures alert someone. |
Total: 100
