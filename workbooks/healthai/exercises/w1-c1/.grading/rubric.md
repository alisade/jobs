# Rubric: healthai/w1-c1 PA intake API with typed requests and the CMS-0057-F clock
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Model design | 15 | Shared base, real discriminated union, validators in the model (not in the route), `extra="forbid"`, strict ints where a string would be a bug, `AwareDatetime` or an explicit check. |
| 3 | Clock correctness and clarity | 15 | Expedited as elapsed hours, standard on the plan's wall clock with `zoneinfo`, QHP exclusion explicit, UTC out, no business-day logic. Comments say which rule each branch implements. |
| 4 | ANSWER.md | 15 | Explains the DST choice and why it matters for a compliance clock, where idempotency state should live in production (Firestore/Redis/Postgres with TTL), timeouts vs retries on eligibility, and that 422 bodies can echo PHI back. |
Total: 100
