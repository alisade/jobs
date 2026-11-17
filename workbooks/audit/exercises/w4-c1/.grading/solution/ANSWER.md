# ANSWER: audit/w4-c1 Durable test run with a review gate

## Approach

Five steps per sample, each committed with its output and the new sample state in one SQLite
transaction. A step with a committed output is skipped forever; crash hooks sit before the work and
between the work and the commit, which is the dangerous window.

## Fix

- run.py: per-step check-work-commit; exceptions stop in awaiting_review without blocking other samples;
  workpaper with a deterministic name and bytes, overwrite=False and a compare on conflict; GRC issue
  with the key run_id/sample_id/grc_issue and an intent record before the call.
- review(): state, SoD and override rules raise ReviewError; the review is committed and logged and
  copied into the workpaper row.
- log.py: hash chain over canonical JSON; reopening continues seq and prev; verify reports edits,
  deletions, insertions and reorders.

## Trade-offs / what I would do in production

The model and test steps are at-least-once (a crash after the call but before the commit repeats the
call); side effects are exactly-once by idempotency. The chain cannot see a truncated tail: write the
head hash to an immutable blob container after every run. Reviewer identity should come from Entra ID
tokens, not a string. On Azure this maps to Durable Functions (orchestrator replay, activities with
the same idempotency keys, external events for the reviewer decision).
