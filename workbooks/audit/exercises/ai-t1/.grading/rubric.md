# Rubric: audit/ai-t1 Gemini cost up after the prompt refactor
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh (4 of the tests are guards that already pass on the starter) |
| 2 | Root cause | 25 | Full: both parts: (a) the per-request run header (run id, start time, sample id) at the top of the system instruction ends the common prefix after a few dozen characters, below the 1024-token minimum, so every call misses; (b) ENABLED_TOOLS is a set, its iteration order depends on PYTHONHASHSEED, so tool declarations (serialized first) differ between the two Function instances. Partial (12): only (a). Zero: model bump or tokenizer blamed. |
| 3 | Evidence | 15 | Full: cached_tokens 0 on all 25 calls after vs ~91% before, prompt_tokens roughly unchanged (so not a tokenizer change), latency tracks uncached tokens, a diff of serialized requests showing where they diverge, and the cross-process comparison. Partial: numbers only. |
| 4 | Red herring | 10 | Rules out the model bump: a model change costs one cold miss per instance, not 25 of 25; prompt token counts are the same; the simulator keys the cache by model and the second call on -002 would hit if the prefix were stable. |
| 5 | Fix and prevention | 15 | Full: static content first (stable tool order, static system instruction), per-request data last in the user content, run metadata to logs/labels; a regression test on prefix stability across hash seeds and an alarm on the cache hit ratio; mentions explicit context caching as the option when the prefix must be guaranteed. Partial: fix only. |
Total: 100
