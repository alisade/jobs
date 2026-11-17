# Reference: audit/w4-t1

**Root cause.** `GrcClient.create_issue` builds `Idempotency-Key = uuid4()` inside the attempt loop.
The GRC deduplicates by key, so every attempt is a new request to it. On 2026-10-01 the gateway
committed two requests whose responses never arrived (commit-then-timeout):

```
02:00:30Z req=r-0001 POST /api/v2/issues key=<k1> -> 201 ISS-7400 (response not delivered ...)
02:01:05Z req=r-0002 POST /api/v2/issues key=<k2> -> 201 ISS-7401 (response not delivered ...)
```

The client saw two timeouts, raised GrcUnavailable, and the orchestrator retried the whole step
("CHG-104390 step attempt 1/3 failed ... retrying step in 60s"), which appended the workpaper row a
second time and sent r-0003 with a third key: ISS-7402. The checkpoint stores only ISS-7402, so the
orchestrator believes it raised one issue. CHG-104611: r-0006 committed ISS-7404 and timed out, the
client retry r-0007 with a new key created ISS-7405.

**Red herring.** r-0004 was a 429 before anything was committed; the client waited Retry-After 2 s
and r-0005 created exactly one issue for CHG-104502. Rate limits cannot create issues.

**Fix** (`.grading/solution/orchestrator/`): the caller passes `idempotency_key = run_id/sample_id/grc_issue`
and the client sends it on every attempt; the orchestrator checkpoints the workpaper step separately,
checks the blob for an existing row before appending (covers a crash between append and checkpoint),
records the intent (key) before the GRC call, and stores the issue id as its own step. After a crash
after commit, the restarted process sends the same key and gets `200 replay`.

**Production.** Close the duplicates through the GRC (not by deleting rows) with a note referencing
this incident, so the auditors see one exception per sample and the trail of what happened; confirm
the GRC keeps keys at least as long as a run can be retried; alarm on replays and on two open issues
with the same run and sample.
