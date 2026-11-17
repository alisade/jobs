# Rubric: audit/w2-c1 CM-03 population, completeness and accuracy checks, and a reproducible sample
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Population definition | 15 | Full: defined from the deploy log (the system that proves a change reached prod), local-date period in the entity time zone, re-deploys collapsed, unmerged/off-main changes kept and flagged with the reason stated. Partial: correct code, reasoning missing. Zero: population filtered by the attribute under test. |
| 3 | IPE argument | 15 | Full: ANSWER.md covers the source and its parameters, who ran the control-total report and when, the reconciliation, the accuracy tests, and why the export itself needs evidence (IPE). Partial: reconciliation only. |
| 4 | Sampling judgement | 10 | Full: CM-03 classified as recurring (multiple per day or at least daily) with 25, when the high-risk 40 applies, seed recorded and reproducible, population hash ties the sample to the exact population. Partial: number without reasoning. |
| 5 | Findings handling | 10 | Full: the two unmerged changes and the missing ticket are carried as items to test (likely exceptions) or reported to the control owner, not deleted; deterministic step kept free of model calls, with the reason. |
Total: 100
