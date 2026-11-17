# Rubric: ms/w7-t1 Purchase orders silently missing from Contoso Parts
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated checks | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: both halves named precisely: retryPolicy none so 429s from the APIM rate limit fail on first attempt, AND the Catch scope handles the failure without Terminate so the run ends Succeeded. Partial (12-18): only one half, or "throttling" without the retry policy. Zero: blames Contoso Parts, the trigger condition, or the connection. |
| 3 | Evidence | 15 | Full: quotes a run id with statusCode 429, Retry-After and empty retryHistory; counts (140 runs Succeeded vs 96 received, 44 x 429 in the APIM log); shows Try Failed / Catch Succeeded / run Succeeded. Partial: some evidence. Zero: assertion only. |
| 4 | Fix quality | 15 | Full: valid retry policy sized against the 60 s window, Catch after Failed+TimedOut, result('Try') captured, PO flagged and/or team notified, Terminate Failed with runError, trigger condition left alone, nothing reordered. Partial: run fails loudly but no notification, or retry only. |
| 5 | Production trade-offs | 10 | Full: idempotency of retries, concurrency/queueing for bursts, reprocessing of failed POs, alerting, environment variables/connection references for ALM. Partial: one or two. Zero: none. |
Total: 100
