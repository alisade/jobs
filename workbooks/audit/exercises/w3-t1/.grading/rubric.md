# Rubric: audit/w3-t1 After the nightly restart the agent re-tests finished samples
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: progress is stored under `temp:completed`; ADK `temp:` keys live only for the current invocation and are never persisted, so every new invocation starts with an empty completed list and next_batch returns the first five again. The comment's assumption ("per-run scratch, fresh run starts clean") is exactly the bug. Partial: "state lost on restart" without the temp prefix. Zero: warnings or 429. |
| 3 | Evidence | 15 | Full: shows the persisted session state (sessions.db) without a completed key, the tested table with 2 rows for CHG-105101..105105, and the duplicate work item; or a minimal reproduction. Partial: reasoning from code only. |
| 4 | Fix and scope choice | 15 | Full: session-scoped key (no prefix) with the reason (progress belongs to this sample's session; user:/app: would leak across sessions or samples); notes test_change should also be idempotent (skip or dedupe on change_id). Partial: fix without reasoning. |
| 5 | Red herrings and impact | 10 | Full: token-usage warnings come from the stand-in model not reporting usage; the 429 was retried successfully; impact: CHG-105103 duplicate work item, five changes tested twice, night-two results for CHG-105106..105110 never produced. |
Total: 100
