# Rubric: fde/w1-t1 cache_read collapsed after a harmless release
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: names the mechanism precisely: set iteration order of str depends on per-process hash randomization (PYTHONHASHSEED), so each worker process emits a different tool order and tool-list line in the static prompt, so the cached prefix (tools -> system -> messages) differs per process and conversations miss when the load balancer moves a session. Partial (10-15): "the set changed the order" without the per-process / multi-worker part, or blames ordering "randomly per request". Zero: blames the SDK bump, the clock, TTL, or Anthropic. |
| 3 | Evidence | 20 | Full: at least two independent pieces, quoted: log lines showing misses on turn openings after a worker change (or dashboard numbers before/after), and a reproduction (two PYTHONHASHSEED values printing different orders or digests). Explains why the single-process pre-deploy check passed. Partial: one piece, or numbers without commands. Zero: assertion only. |
| 4 | Red herrings handled | 5 | Explicitly rules out the SDK bump and the hourly clock (after the breakpoint), with a reason. |
| 5 | Fix quality | 10 | Order from TOOL_ORDER (or another fixed sequence), dedupe and extra_tools kept, unknown extras still fail, static prompt line consistent; no PYTHONHASHSEED pinning as the fix; no sorting alphabetically (changes the shipped order the evals were tuned on) unless justified. |
| 6 | Prevention / production | 10 | Concrete: multi-seed prefix test or golden prefix digest in CI, per-worker prefix digest logged at start-up, hit-rate alert per release, review rule against set iteration on prompt paths. Partial: generic "add tests". |
Total: 100
