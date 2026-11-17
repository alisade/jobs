# Rubric: healthai/ai-c1 Eval gate in CI for the PA assistant
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Gate design | 15 | Hard gates (schema, safety) are not averaged; statistical gates use a confidence bound; invalid rows cannot inflate accuracy; code is readable and each gate testable alone. |
| 3 | CI ergonomics | 10 | Summary names the failing gate, values, thresholds and violations; exit code drives the build; cost and latency reported next to quality. |
| 4 | ANSWER.md | 20 | Discusses N and z vs flakiness and cost, baseline update process with approval, limits of substring citation checks and how to calibrate a judge, PHI rules for eval data, and where the gate runs (GitHub Actions, Gen AI evaluation service). |
Total: 100
