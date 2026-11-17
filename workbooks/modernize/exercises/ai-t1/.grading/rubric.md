# Rubric: modernize/ai-t1 Prompt caching never hits
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (1 visible and 2 hidden tests already pass) |
| 2 | Root cause identified | 25 | Full: commit 7a1c9e2 (2026-11-05) put `now.isoformat(timespec='seconds')` inside the cached system block, so the prefix changes on every request: every turn writes about 32k tokens to the cache and none reads; the dashboard flips to cache_read 0 from 2026-11-06 (half a day on the 5th). Also names the latent cross-process instabilities: the file listing from a set (POD-209) and skills in glob order (POD-207), which break sharing between CI jobs. Partial (10-15): the timestamp only. Zero: the model. |
| 3 | Evidence | 20 | Full: dashboard rows before and after, the git log commit and time, `make replay` showing cache_write every turn, the arithmetic that 11M cache-write tokens at 3.75/M explains the 4x. Partial: one or two. |
| 4 | Red herring handled | 10 | The model bump: same prices (pricing note), and it landed before the cache break (11:03 vs 16:12); token counts per request are unchanged, only the cache columns move. |
| 5 | Fix and guard | 15 | Full: static content before the breakpoint, sorted and deterministic; dynamic content (time, per-turn state) after it; a CI check that hashes the prefix across two builds or alerts on cache hit rate below a threshold; notes on TTL and moving the breakpoint forward in long sessions. Partial: fix only. |
Total: 100
