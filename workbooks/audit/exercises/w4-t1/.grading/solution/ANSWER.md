# ANSWER: audit/w4-t1 Duplicate GRC issues after a retry

## Approach

Lined up incident/orchestrator.log and incident/grc-gateway.log by timestamp, then read the client
code for how the Idempotency-Key is produced.

## Root cause

The GRC client generates a new uuid4 Idempotency-Key on every attempt. Two requests for CHG-104390
were committed by the gateway but their responses were lost:
`02:00:30Z req=r-0001 ... -> 201 ISS-7400 (response not delivered ...)` and
`02:01:05Z req=r-0002 ... -> 201 ISS-7401 (response not delivered ...)`, with different keys. The client
saw two timeouts and gave up; the orchestrator retried the whole step
(`CHG-104390 step attempt 1/3 failed ... retrying step in 60s`), appended the workpaper row again and
sent r-0003 with a third key (ISS-7402). Only ISS-7402 reached the checkpoint. CHG-104611: r-0006
committed ISS-7404 and timed out, r-0007 created ISS-7405. The checkpoint is written only after the
whole step returns, so nothing recorded the earlier attempts.

The 429 is not involved: r-0004 was rejected before commit, the client waited the 2 s Retry-After
and r-0005 created exactly one issue for CHG-104502.

## Fix

Deterministic key run_id/sample_id/grc_issue passed by the orchestrator and reused by the client on
every attempt; intent logged and checkpointed before the call; workpaper as its own checkpointed step
with a check for an existing row. `make replay`: 3 issues for 3 exceptions, 6 rows; the hidden-fault
tests (commit-then-timeout, lost requests, crash after commit and restart) pass.

## Trade-offs / what I would do in production

Close ISS-7400, 7401 and 7404 in the GRC as duplicates with a reference to this incident so the
auditors see the history. Confirm the GRC's key retention covers the longest retry window. Alarm on
200-replays and on more than one open issue per run and sample.
