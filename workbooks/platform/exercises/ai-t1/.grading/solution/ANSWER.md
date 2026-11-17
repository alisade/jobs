# ANSWER: platform/ai-t1

## Approach

Ran `make repro`, compared the transcript, PR body and the reviewer's plan, then read verify and tools.

## Root cause

verify.verify used the model's plan_summary as its counts (transcript: verify input "model
plan_summary", ok true). The model's input was terraform_plan's raw JSON cut at 8000 characters; the plan
is 14706 characters and the riq_main `["delete","create"]` change sits near character 13300, so the model
saw 8 imports and no replace (PR: "8 to import", ticket: 14). The prompt's "be concise" is not it: the
model reported what it saw.

## Fix

Counts computed from the full plan file; replace in both orders counts as add and destroy; fail closed on
bad, truncated or errored plans; the claim is ignored; the tool returns a compact complete summary; the
PR body uses verified counts. Repro: no PR, 14 import, 1 add, 1 destroy, 1 replace.

## Trade-offs / what I would do in production

The apply pipeline runs the same gate; evals with dirty plans; alert on claim/plan disagreement; tool
outputs designed for context limits rather than sliced.
