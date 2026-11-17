# Rubric: edgefde/w3-c1 Champion/challenger promotion gate
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Gate semantics | 15 | Full: both models evaluated fresh on the same pinned holdout, floors plus not-worse plus strictly-better, ties rejected, aliases only move on promote, previous-champion kept. Partial: compares against stored metrics or allows ties. |
| 3 | Fail closed | 10 | Every error path (hash, artifact, missing alias, empty class) returns 2 / raises before any alias change; no broad except that turns errors into a promotion or a silent reject. |
| 4 | Reviewer output | 10 | PR comment is readable: both versions, holdout hash, counts, decision and reasons in plain words. |
| 5 | Judgement in ANSWER.md | 15 | Explains each rule's failure mode, notes 278 fault windows makes a 0.01 recall difference noise (bootstrap CI or a minimum margin), per-machine slices, shadow/canary on gateways, drift after promotion, and maps to MLflow aliases and a CI job. |
Total: 100
