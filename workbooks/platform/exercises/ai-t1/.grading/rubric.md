# Rubric: platform/ai-t1 The agent's PR said no-op, the plan had a replace
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: `verify.verify` builds its counts from the model's `plan_summary`, so the gate verifies the model's claim, not the plan; and `tools.terraform_plan` returns the raw plan JSON cut at 8000 characters, so the model only saw the first 8 imports and never saw the `["delete","create"]` change for riq_main (it starts near character 13300). Two parts, one root cause: "verification" trusted model output. Partial (10-15): one of the two. Zero: the prompt. |
| 3 | Evidence | 20 | Full: transcript (chars 8000 vs plan 14706, verify input "model plan_summary"), the PR body's 8 vs the ticket's 14, the reviewer's plan line, the position of the replace in the JSON, repro output. Partial: one or two. |
| 4 | Red herring handled | 5 | "Be concise" changes nothing: the model counted correctly what it was shown; a prompt can make it less likely to omit, never impossible. |
| 5 | Fix quality | 15 | Counts from the plan file with both replace orders, fail closed on bad input, the claim ignored (optionally logged as a disagreement), compact complete tool output, PR body from verified counts. |
| 6 | Prevention | 5 | Pipeline-side plan gate before apply (so a bad PR cannot apply even if merged), evals with dirty plans, alert on disagreement between claim and plan, tool outputs designed for context limits. |
Total: 100
