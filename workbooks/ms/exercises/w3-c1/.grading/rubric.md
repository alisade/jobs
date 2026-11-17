# Rubric: ms/w3-c1 Lakehouse table maintenance job (OPTIMIZE, Z-order, VACUUM guard)
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Safety | 15 | Full: retention guard checked before any rewrite, honors the table property, override is explicit, dry run truly side-effect free. Partial: guard present but checked after OPTIMIZE or ignores the table property. Zero: can delete inside the 7-day window by default. |
| 3 | Targeted optimization | 10 | Full: per-partition planning with partition filters, no rewrite of healthy tables/partitions, idempotent. Partial: compacts whole table whenever any threshold is hit. |
| 4 | Code quality and report | 10 | Clear structure, useful reasons in the plan, JSON report usable by alerting, per-table error isolation. |
| 5 | ANSWER.md and Fabric mapping | 15 | Explains V-Order vs Z-order vs bin-compaction, when V-Order matters (Direct Lake, SQL endpoint), scheduling and CU cost, the retentionDurationCheck setting and why the RETAIN 0 HOURS incident broke readers. |
Total: 100
