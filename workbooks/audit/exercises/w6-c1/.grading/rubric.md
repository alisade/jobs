# Rubric: audit/w6-c1 Eval harness per control: accuracy, exception recall, consistency, cost and a CI gate
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Metric judgement | 10 | Full: undefined values are None (not 0 or 1), duplicates and unlabeled rows handled deliberately, kappa only over complete subjects, severity tie-break explained. Partial: correct code without reasons. |
| 3 | Interpretation of v3 and v4 | 15 | Full: v4 blocked because overall exception recall falls from 29/30 to 20/30 (self-approval via e-mail alias missed on S004 and S027, independent_approver recall 3/15) and accuracy drops to 0.90; notes v4 is cheaper (about $0.075 vs $0.087 per 100) and perfectly consistent yet wrong, and why neither matters; reads S025 (needs_review sample answered pass in 2 of 5 runs: a consistency problem that hides an unresolved identity) and S017 (missing run is a data-completeness finding, not a silent drop). Partial: blocked/not blocked without the attribute-level why. |
| 4 | Statistical honesty | 10 | Full: 30 samples / 30 exception run-rows give wide intervals (e.g. Wilson interval for recall), a gate on recall per attribute, more labeled exceptions, inter-rater check on the human labels. Partial: mentions sample size only. |
| 5 | Production use | 10 | Full: gate in CI on prompt/model/config change, baseline updated only with sign-off, report kept as audit evidence, cost per 100 samples tracked per release. Partial: "run it in CI". |
Total: 100
