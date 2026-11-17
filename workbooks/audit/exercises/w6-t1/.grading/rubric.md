# Rubric: audit/w6-t1 "97% accuracy" on the dashboard, 4 missed exceptions in review
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 25 | Full: on 2026-10-30 `make refresh-golden` rebuilt labels/golden.jsonl from runs/replay-2026-10-30.jsonl (model outputs, labeled_by model:gemini-3.8-flash, labeled_at 2026-10-30T22:14:07Z) after the loader started requiring control_id; the human labels were replaced, so the harness scores the agent against its own earlier output. The replay misses the same four exceptions as production, so they look correct; 29/30 agreement = 96.7%, and the golden set only "contains" 3 exceptions, all found = 100% recall. Partial: "labels are wrong" without the mechanism. Zero: blames prompt v3.2 or the model. |
| 3 | Evidence | 15 | Quotes the provenance fields from golden.jsonl vs human_v1, the changelog entries and refresh log, and before/after dashboard output (true: 26/30 = 86.7%, recall 3/7 = 42.9%, missed Q3-03, Q3-11, Q3-19, Q3-26). |
| 4 | Fix quality | 15 | Labels restored by migrating human_v1 (provenance kept, control_id added), loader refuses non-human provenance with a clear error, refresh script cannot source labels from runs; does not weaken schema checks. Partial: only restored the file. |
| 5 | Secondary finding and process | 15 | Identifies the cost bug as separate: prices are per 1M tokens but score.py divides by 1,000 (1000x, about $0.084 not $84 per 100); fixes or explains it. Process: ground truth changes need reviewer sign-off (labels are evidence), CODEOWNERS/approval on labels/, eval reports carry the golden-set hash and provenance summary, prior dashboard figures withdrawn and the steering committee told. Partial: one of the two. |
Total: 100
