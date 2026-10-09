# Rubric: ms/w6-c2 Dataverse Web API sync client
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh |
| 2 | Service protection handling | 15 | Full: honours Retry-After per attempt, bounded retries, cap on a single wait, no retry of 4xx, no hot loop, retry wraps every call incl. $batch and nextLink pages. Partial: retries but ignores Retry-After or retries everything. Zero: no retry or unbounded loop. |
| 3 | Change tracking correctness | 15 | Full: deltaLink used verbatim, deletes detected by the $deletedEntity context, token saved only after the last page is applied, sensible plan for an expired token (full resync). Partial: works but saves token early or parses the link. Zero: re-imports everything each run. |
| 4 | Upsert and batch semantics | 10 | Full: correct If-Match / If-None-Match, quote escaping, key not in body, created vs updated via return=representation, one atomic change set with Content-ID and failing index. Partial: one of these missing. Zero: POST-based create or non-atomic batch. |
| 5 | Code quality | 5 | Readable, small helpers, typed, no dead code, errors carry status and Dataverse error code. |
| 6 | ANSWER.md trade-offs | 10 | Full: concrete reasoning on retry budget vs 5-minute sliding window, expired tokens (ExpireChangeTrackingInDays), when CreateMultiple/UpsertMultiple beat $batch, MSAL client credentials for an application user, telemetry. Partial: generic. Zero: empty. |
Total: 100
