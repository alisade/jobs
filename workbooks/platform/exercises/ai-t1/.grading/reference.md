# Reference: platform/ai-t1

Root cause: the gate verified the model, not the plan. `verify.verify` copied the model's plan_summary
into its counts. The model's view was incomplete because `tools.terraform_plan` returned the raw plan
JSON sliced to 8000 characters (transcript: chars 8000, plan 14706); the replace of riq_main sits near
character 13300, after the first 8 imports, so the model honestly reported 8 imports and nothing else.
"Be concise" is a red herring: the model summarized exactly what it saw.

Fix (`.grading/solution/agent/`): `summarize()` counts from the full plan (replace in either order counts
as add + destroy), `verify()` fails closed on unreadable, incomplete or errored plans and unknown actions,
ignores the claim (logs a disagreement); `terraform_plan` returns a compact JSON summary (counts plus
replaced/destroyed/changed addresses) that never needs truncation; the PR body uses verified counts.

Prevention: the apply pipeline runs the same gate on its own plan; evals with dirty plans; alert when the
model's claim and the plan disagree; design tool outputs to fit context instead of slicing.
