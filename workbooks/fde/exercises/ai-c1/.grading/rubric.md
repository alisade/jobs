# Rubric: fde/ai-c1 Eval suite for a misbehaving shopping agent
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 45 | points = 45 * passed / total from grade.sh |
| 2 | Check design and false-positive control | 15 | Full: every check scopes by event order and turn (latest user message, results before the call), ignores user text and tool-result text where the rule is about the assistant, matches ids as whole tokens, treats errored results as non-evidence. Partial: right on fixtures but naive substring/whole-transcript scans. Zero: checks that pass on the crafted traps. |
| 3 | Judge determinism and failure handling | 15 | Full: prompt built only from transcript content with sorted, compact JSON; temperature 0; verdict parsed from prose/fences; a missing recording or unparseable reply is `errored`, never a pass, never a crash; ANSWER.md explains why an errored judge must be visible separately from an agent failure. Partial: deterministic but errors swallowed as fail. Zero: random or time-dependent prompt, or judge errors counted as passes. |
| 4 | Aggregation correctness | 10 | Full: unbiased pass@k = 1 - C(n-c,k)/C(n,k) and pass^k = C(c,k)/C(n,k), input validation, flaky = 0 < c < n, stable ordering, errored checks excluded from failure counts. Partial: one formula or edge case wrong. Zero: pass@k computed as pass rate. |
| 5 | Code quality | 5 | Small pure functions, shared helpers instead of copy-pasted scans, typed, readable details on failures (event index). |
| 6 | ANSWER.md analysis and trade-offs | 10 | Full: reads the summary like an owner (what to fix first: the always-failing checkout staging, then provenance), says why pass^k is the release gate for a commerce agent, and covers judge calibration and run count. Partial: generic. Zero: empty. |
Total: 100
