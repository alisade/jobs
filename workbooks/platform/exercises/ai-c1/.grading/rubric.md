# Rubric: platform/ai-c1 On-call page triage assistant with an eval gate
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh |
| 2 | Enforcement in code | 20 | Full: schema validation before execution, unknown tool and failures as is_error, write tools only with approval, approver exceptions fail closed, audit for every write attempt, nothing depends on the system prompt for safety. Partial: approval check present but fails open on exceptions or is keyed on prompt text. Zero: relies on instructions. |
| 3 | Output contract and fail-closed | 10 | Full: note validated by the Pydantic model, evidence checked against executed calls, one retry with the error, then needs_human; max_turns. Partial: retry without grounding check. |
| 4 | Eval design | 10 | Full: safety separate from quality and never averaged away; s07 left failing and explained; gate thresholds justified. Partial: single pass/fail. |
| 5 | ANSWER.md production judgement | 15 | Full: read-only credentials for the assistant, approval outside the model's reach, injection through alert annotations as untrusted content, growing the golden set from real pages, tracing (OTel GenAI spans), cost and latency per page, how it fits the 12-hour rotation. Partial: generic. |
Total: 100
