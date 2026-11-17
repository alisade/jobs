# Rubric: audit/w4-t1 Duplicate GRC issues after a retry
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (4 of the tests are guards that already pass on the starter) |
| 2 | Root cause | 25 | Full: the client generates a new uuid4 Idempotency-Key on every attempt, so a commit-then-timeout (server committed ISS-7400/7401, response lost) plus a retry creates a new issue; the step retry after GrcUnavailable re-runs the whole step, re-appending the workpaper row and creating a third issue; the checkpoint is only written after the step returns. Partial: "retries cause duplicates" without the key or the commit-then-timeout mechanism. Zero: rate limiting or the GRC blamed. |
| 3 | Evidence | 20 | Full: quotes gateway lines r-0001/r-0002 (201 committed, response not delivered, different keys), r-0003, r-0006/r-0007 for CHG-104611, the orchestrator's "step attempt 1/3 failed" line, and the two workpaper rows; ties times across both logs. Partial: some lines, no correlation. |
| 4 | Red herring | 10 | Rules out the 429: r-0004 was rejected before commit, the client honored Retry-After 2 s, CHG-104502 has exactly one issue; a higher quota would change nothing. |
| 5 | Fix quality and production | 15 | Full: deterministic key from run, sample and step reused on every attempt and restart, intent recorded before the call, workpaper step checkpointed and deduplicated; ANSWER.md covers cleanup of the existing duplicates through the GRC with a note for the auditors, key retention window on the server, and an alarm on 200-replays or duplicate titles. Partial: key fixed only. |
Total: 100
