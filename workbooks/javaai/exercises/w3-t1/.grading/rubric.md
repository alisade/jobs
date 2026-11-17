# Rubric: javaai/w3-t1 "Generate quiz" fails for biology, history and psychology lessons
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (several rows are regression guards) |
| 2 | Root cause identified | 25 | Full: release 2.3 (PLAT-3317) set every safety category to BLOCK_LOW_AND_ABOVE by copying the kids profile; ordinary course answers rated LOW (pathogens, propaganda, war poetry, substance use) are now blocked: the candidate comes back with finishReason SAFETY and no content (or, for blocked prompts, promptFeedback.blockReason and no candidates); service.py indexes candidates[0].content.parts[0].text and raises KeyError, which FastAPI returns as 500. Partial (10-15): only the config or only the KeyError. Zero: quota, retries, dependency bumps. |
| 3 | Evidence | 20 | Quotes the diff, the KeyError tracebacks ('content' and 'candidates'), the per-lesson 500 counts by subject, a reproduced raw response showing finishReason SAFETY with blocked: true, and the Sunday errors all being chem-330-l2 (HIGH rating, blocked under the old profile too: the latent handling bug). |
| 4 | Red herring handled | 10 | 429s present on both days at a similar rate, each followed by success on retry; quota peak at 31% of limit; 429s are shared PayGo capacity. More retries would add latency and cost and fix nothing. |
| 5 | Fix quality | 10 | Thresholds restored per category (not BLOCK_NONE), typed blocked result with source and category, 422 with a learner/author-facing message, no stack traces, defensive handling of missing parts. |
| 6 | Production follow-ups | 5 | Separate safety profiles per product/audience with review, blocked-rate metric per category and alert, eval set of "must not be blocked" lessons in CI, Model Armor for prompt screening, change management for safety config. |
Total: 100
