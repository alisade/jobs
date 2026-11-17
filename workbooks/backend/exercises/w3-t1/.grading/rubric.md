# Rubric: backend/w3-t1 The partner sync is missing contacts
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: the sort/filter key `created_at` is not unique; the bulk import created 500 rows with one timestamp; the cursor carries only `created_at` and `>` skips the rest of the tied group (462 rows); tie order is nondeterministic. Partial: "pagination bug" or "ties" without the mechanism. Zero: blames rate limiting, the partner client, or SQLite. |
| 3 | Evidence | 20 | Full: quotes the replica count of 500 rows at one timestamp, the two access-log lines where the cursor jumps past the import timestamp, the partner's missing=462, and the make repro numbers before and after. Partial: one of these. |
| 4 | Red herring | 5 | Explains why the 429s cannot lose rows (same cursor retried, full pages returned). |
| 5 | Fix quality | 10 | Unique stable sort (created_at, id), row-value seek, opaque validated cursor, 400 problem on bad cursor, limit bounds, index matches the sort. Deduct for `>=` with duplicates, offset pagination, or a cursor that exposes raw values without validation. |
| 6 | Production follow-up | 5 | Resync advice for the partner, cursor versioning or signing, a regression test with ties, monitoring of reconciliation drift. |
Total: 100
