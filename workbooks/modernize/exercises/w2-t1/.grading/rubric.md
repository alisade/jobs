# Rubric: modernize/w2-t1 The reverse-engineer skill missed the batch job's tables
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (2 visible tests are guards that already pass) |
| 2 | Root cause identified | 25 | Full: `render()` silently cut the hit list at 200 lines (`lines[:limit]`, no total, no marker); hits are sorted by path, so every reporting-batch hit (and the batch-only tables) fell after line 200; the model reported faithfully what the tool showed and then over-generalised absence; the skill told it to record "every table it reports". Partial (10-15): "output was truncated" without the sort-order mechanism or without the skill's part. Zero: hallucination or context window. |
| 3 | Evidence | 20 | Full: transcript tool_result `lines: 200` and the last line inside claims-web; total 314 hits from a full run; the 9 tables in the spec vs 14 in the repo; `context_used_pct: 31` refuting the context theory; `grep` showing LOSS_TRIANGLE only in reporting-batch. Partial: one or two. |
| 4 | Red herring handled | 10 | Rejects "bigger model": the model never received the batch hits; a bigger model would produce the same spec. Notes the real model error was claiming absence without proof, which the skill now forbids. |
| 5 | Fix and prevention | 15 | Full: complete summary plus paging with an explicit TRUNCATED line and next offset; skill verification step comparing inventory against the summary; failure-mode log entry; a general rule for agent tools (state totals, never truncate silently, return actionable continuation); eval case with a repo larger than one page. Partial: just a bigger limit. |
Total: 100
