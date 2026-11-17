# Rubric: aiarch/x-1 Session table throttles at 09:00
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: single-value GSI partition key ACTIVE is a hot partition; GSI throttling back-pressures base-table writes even on on-demand. Zero: capacity mode. |
| 3 | Evidence | 15 | WriteThrottleEvents on the GSI dimension vs modest table consumption, the key schema, status counts, app error text. |
| 4 | Fix quality | 10 | Stable write sharding, sparse index, paginated fan-out query, TTL and billing unchanged. |
| 5 | Production view | 10 | Why capacity changes do not help, live GSI migration, Contributor Insights, shard sizing. |
Total: 100
