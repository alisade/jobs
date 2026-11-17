# ANSWER: audit/w6-t1 "97% accuracy", 4 missed exceptions

## Approach

Compared the reviewer's 7 exceptions with the golden set the dashboard uses: golden.jsonl only marks
3 samples as exceptions. Looked at provenance on the rows, then at the repo history and refresh log.

## Root cause

`labels/golden.jsonl` is not human ground truth. Every row reads
`"labeled_by": "model:gemini-3.8-flash", "labeled_at": "2026-10-30T22:14:07Z"`, while
`labels/human_v1/cm03-golden-v1.jsonl` rows read `human:r.okafor` / `human:s.lindqvist`, July 2026.
`incident/changelog.txt`: on 2026-10-30 the loader started requiring control_id and
`make refresh-golden` "refreshed" the set; `incident/refresh-golden.log`: "wrote 30 rows to
labels/golden.jsonl from runs/replay-2026-10-30.jsonl". scripts/refresh_golden.py builds labels from
the replay's model outputs. So the dashboard graded the agent against itself: the replay makes the
same four mistakes as production (Q3-03, Q3-11, Q3-19, Q3-26), they count as correct, giving 29/30 =
96.7% and recall 3/3.

## Fix

Migrated human_v1 into labels/golden.jsonl (control_id added, labels and provenance unchanged).
load_golden raises ProvenanceError on any non-human row; refresh_golden.py now migrates in place and
refuses non-human rows. True Q3: accuracy 26/30 = 86.7%, exception recall 3/7 = 42.9%, missed Q3-03,
Q3-11, Q3-19, Q3-26, matching the reviewer. Secondary: the cost figure divides per-1M prices by
1,000; fixed, about $0.084 per 100 samples, consistent with the $3.12 invoice. Unrelated to accuracy.

## Trade-offs / what I would do in production

Labels are evidence: approvals on labels/ by a reviewer, eval reports stamped with the golden-set
hash and provenance counts, and the October figures withdrawn in writing. The agent's real gap (alias
resolution for SoD, linked change) goes into the backlog with these four samples as regression cases.
