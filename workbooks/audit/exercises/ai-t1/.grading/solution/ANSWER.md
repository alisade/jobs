# ANSWER: audit/ai-t1 Gemini cost up after the prompt refactor

## Approach

Compared usage-before and usage-after per call, then printed serialize_request() for two samples and
for one sample in two processes with different PYTHONHASHSEED values.

## Root cause

cached_tokens is 0 on all 25 calls after the release (before: ~91% of input tokens cached), while
prompt_tokens stays ~5,360, so the input did not change size: the prefix did. Two causes:
1. The run header "ControlPilot run CM03-2026Q3-R2 | started ... | sample CHG-..." is the first line
   of the system instruction. Requests diverge at the sample id, a few dozen characters in, far below
   the 1,024-token minimum cached prefix.
2. ENABLED_TOOLS is a set; its order depends on PYTHONHASHSEED, so the two Function instances serialize
   the tool declarations (the first part of the prefix) in different orders.

The model bump is not the cause: a new model costs one cold call per instance and then hits; here
every call misses, and the token counts did not change.

## Fix

Tools declared from an ordered, sorted tuple; the system instruction is the static procedure only;
the sample stays in the last user content and the run metadata moves to the logs. make replay:
cache hit ratio back to ~0.95, $0.07 per 100 samples, p50 ~183 ms; tests pass across hash seeds.

## Trade-offs / what I would do in production

Add the cross-seed prefix test to CI and an alarm when the batch cache hit ratio drops below 0.7.
Consider explicit context caching for the static procedure when it must be guaranteed. Report cost
per control in the eval report so a regression like this shows up before FinOps does.
