# ANSWER: audit/w3-t1 The nightly tester re-tests finished samples

## Approach

Counted tests and work items in run/queue.db, then read the persisted session in run/sessions.db,
then reproduced the problem with two processes against an empty run directory.

## Root cause

Progress is stored under `temp:completed`. ADK drops temp: keys at the end of each invocation and
never persists them, so night two starts with no progress. The queue shows CHG-105101..105105 tested
twice and two work items for CHG-105103. The persisted state of session cm03-2026Q3 has no
completed key. The token-usage warnings come from the stand-in model omitting usage. The 429 was
retried successfully.

## Fix

`COMPLETED_KEY = "completed"` is session-scoped, so ADK persists it with the session. After the fix,
two nights test all 10 changes once each, with one work item per exception (105103, 105107,
105109), and a third night tests nothing.

## Trade-offs / what I would do in production

Close the duplicate CHG-105103 item and re-run night two for CHG-105106..105110. Also make
test_change idempotent (unique work item per sample and change). Add a test that runs two
invocations through separate session-service instances.
