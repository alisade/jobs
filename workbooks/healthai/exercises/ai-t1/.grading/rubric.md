# Rubric: healthai/ai-t1 A denial finalized with no reviewer on record
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause and evidence | 40 | Full: `tool_finalize_determination` authorizes adverse outcomes from the model-supplied `reviewed` argument instead of server-side state; the injected "SYSTEM NOTE" in DOC-77 (provider-supplied, untrusted) told the model to pass `reviewed=true`, and the tool trusted it. Transcript lines quoted. Partial: injection found but blamed on the model or the prompt. Zero: "the model was tricked" with no code cause. |
| 3 | Red herring | 10 | Explains that a system prompt line is a mitigation the model may ignore, not a control; enforcement must be server-side; may still add it as defence in depth. |
| 4 | Fix and prevention | 20 | Server-side authorization only, outcome must match the reviewer, refusals audited and returned as errors, documents marked untrusted. Prevention: remove or scope the finalize tool, a deterministic hook, injection cases in the eval suite, screening (Model Armor) as an extra layer, audit query kept as a detective control. |
Total: 100
