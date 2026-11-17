# Rubric: audit/w4-c1 Durable test run with a human review gate and a hash-chained execution log
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Exactly-once reasoning | 15 | Full: commits after the work, idempotent side effects (deterministic key, overwrite=False plus compare), explains that the model steps are at-least-once but committed steps are never repeated, and why commit-then-crash is safe. Partial: works, explanation vague. Zero: relies on "it will not crash". |
| 3 | Review gate as a control | 15 | Full: rules enforced in code, not UI; override needs reason and evidence; decision recorded in store, workpaper and log; preparer/reviewer SoD; ANSWER.md notes real identity (Entra ID) instead of strings. Partial: rules present, recording incomplete. |
| 4 | Log integrity | 10 | Full: chain continues across restarts; verify finds edits, deletes, reorders; ANSWER.md says tail truncation is undetectable without an external anchor and proposes one (immutable blob, periodic head hash to GRC). Partial: chain works, limits not discussed. |
| 5 | Production mapping | 10 | Full: maps the design to Durable Functions or Temporal or a LangGraph checkpointer (replay, activities, idempotency) with one concrete trade-off. Partial: names a tool only. |
Total: 100
