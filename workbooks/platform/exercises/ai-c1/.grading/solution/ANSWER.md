# ANSWER: platform/ai-c1 On-call page triage assistant

## Approach

All guarantees live in code: schema checks, approval for writes, grounding of evidence, retry policy.
The prompt only describes the task.

## Fix

run_tool validates input, gates writes behind the approver (exceptions mean no) and audits them;
errors become is_error results. run_triage is bounded, validates the note, retries once, then fails
closed. score separates safety from quality; gate needs zero safety violations.

## Trade-offs / what I would do in production

Read-only service account for the tools; the silence API behind a separate approval service the model
cannot reach. s04 shows untrusted alert annotations steering the model: the gate, not the prompt,
prevents harm. Keep s07 failing until the model or prompt improves. Grow the golden set from real pages,
trace with OTel GenAI spans, track cost and latency per page.
