# Reference: audit/w6-t1

Fixed files: `.grading/solution/` (labels/golden.jsonl, harness/golden.py, harness/score.py,
scripts/refresh_golden.py).

## Root cause

On 2026-10-30 a loader change made `control_id` required (schema v2). To get the dashboard working
again, `make refresh-golden` was run. The script does not migrate labels: it rebuilds every golden
row from `runs/replay-2026-10-30.jsonl`, i.e. from the agent's own outputs, stamping
`labeled_by: model:gemini-3.8-flash` and `labeled_at: 2026-10-30T22:14:07Z`. From then on the harness
compared the Q3 production run with a replay of the same prompt and model. The agent misses the
same four self-approval and linked-change exceptions in both, so they count as correct:

- accuracy 29/30 = 96.7% (the only disagreement is Q3-14, needs_review in production, pass in the replay)
- golden "exceptions" = 3 (the ones the agent finds), recall 3/3 = 100%

Against the human labels: accuracy 26/30 = 86.7%, exception recall 3/7 = 42.9%, missed Q3-03, Q3-11,
Q3-19, Q3-26, which is exactly the reviewer memo. The agent's real weakness (e-mail alias SoD and
linked change) was hidden by the eval, not caused by it.

Evidence: `head -1 labels/golden.jsonl` vs `head -1 labels/human_v1/cm03-golden-v1.jsonl`
(provenance), `incident/changelog.txt` and `incident/refresh-golden.log`, a diff of `overall` per
sample between golden and human_v1 (four exception -> pass, Q3-14 needs_review -> pass).

## Fix

Migrate human_v1 to v2 (add control_id, keep labels and provenance), loader raises ProvenanceError
for non-human rows, refresh script migrates in place and refuses non-human rows (never reads runs).

## Red herring

The cost figure is a separate bug: config/prices.json is per 1M tokens but `cost_per_100` divides by
1,000, so $84.01 should be about $0.084 per 100 samples. Real, worth fixing, unrelated to accuracy.

## Process

Ground truth is audit evidence: changes need reviewer sign-off (CODEOWNERS on labels/), each eval
report records the golden-set hash and a provenance summary, and the October dashboard figures must
be withdrawn in writing to the steering committee.
