# ANSWER: healthai/w4-t1 A reviewer's decision lands on another member's case

## Approach

`make repro` shows all three submissions (0002, 0003, 0008) producing determinations on PA-2026-0008. The
audit export has three decision_received receipts with the right case ids and three determination events
all for 0008.

## Root cause

`review_service.py` keeps a module-level `RUN_CONFIG` (PA-2290). `submit_decision` writes the thread id
into it, then awaits the audit write, then resumes with the shared dict. Every coroutine overwrites the
thread id before any of them resumes, so all resumes hit the last case set. The thread id scheme is
`pa:<case_id>` and is not the cause.

## Fix

Build `config_for(case_id)` inside each call; raise if the resumed determination is for another case.
Tests run five random interleavings of five reviewers; repro now shows each decision on its own case.

## Trade-offs / what I would do in production

Tell Privacy: md-007's denial and rn-104's approval were recorded on member M-100204's case 0008; no
letter was mailed. Repair 0008 by forking from the checkpoint before the first bad resume and re-queue
0002 and 0003. Add idempotency keys to decision submissions and a concurrency test in CI.
