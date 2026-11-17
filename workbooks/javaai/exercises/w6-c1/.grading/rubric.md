# Rubric: javaai/w6-c1 Tune or prompt? Build the tuning set and pick a model with numbers
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Dataset hygiene | 10 | Normalized-stem dedupe, leakage check against held-out content (not only exact stems), hash-based deterministic split independent of input order, a report of what was dropped. |
| 3 | Scoring correctness | 10 | Strict schema (bool is not an int), invalid outputs still cost, nearest-rank percentiles, matching by id. |
| 4 | Decision quality in ANSWER.md | 20 | Picks tuned Flash-Lite (or argues against it with numbers): ~11x cheaper per 1,000 than few-shot, 1.0 valid, 0.90 correct, best grounding, lowest p50; notes 50 items means +-~8 points uncertainty, the few-shot p95 (10 s) from long prompts, that the tuned model was trained on an earlier draft (re-tune on the clean set before shipping), serving costs of a tuned endpoint, that tuning teaches format and style while new facts belong in RAG, and a next measurement (judge rubric for distractor quality, human review sample). |
| 5 | Code quality | 5 | Small functions, no duplicated parsing, readable report. |
Total: 100
