# Rubric: ms/w1-c1 Medallion incremental load with watermark, MERGE and SCD2
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Incremental correctness design | 15 | Full: watermark committed last, never backwards, lookback reasoning explained, idempotency argued (dedupe + guarded MERGE). Partial: works but watermark/commit order or lookback rationale unclear. Zero: full reload or watermark advanced before writes. |
| 3 | MERGE and SCD2 quality | 15 | Full: guarded MERGE predicate (no late overwrite), SCD2 processes all batch changes in order, null-safe compare, no empty commits; uses Delta MERGE rather than overwrite for silver. Partial: correct results but overwrite-everything or O(n^2) Python loops over large frames without comment. Zero: dedup-only SCD2 or wrong effective ranges. |
| 4 | Code quality | 10 | Readable, typed, small functions, no dead code, errors raised with useful messages. |
| 5 | ANSWER.md and Fabric mapping | 10 | Explains how this runs in Fabric (MERGE INTO / DeltaTable API, notebook parameters, pipeline orchestration), trade-offs (lookback cost, back-dated SCD2, OPTIMIZE/V-Order after many small MERGE commits). |
Total: 100
