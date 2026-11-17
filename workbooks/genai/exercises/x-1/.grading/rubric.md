# Rubric: genai/x-1 Ship the assistant into the existing storefront behind a flag
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Rollout design | 15 | Full: salted stable hash for buckets (not `Math.random`, not per-render), kill switch evaluated first, live subscription with cleanup, a mode change aborts in-flight work. Partial: works on mount but needs a reload to react, or re-buckets users between sessions. |
| 3 | Fallback and lifecycle | 15 | Full: TTFT timer cleared when the first token arrives or the request ends, the request is actually aborted on fallback and kill, no state writes from a stale shadow run, legacy results never blocked by the assistant. Partial: fallback shows but the stream keeps running. |
| 4 | Privacy in analytics | 10 | Allowed-field schema enforced in one place, no query text or user id, ANSWER.md is honest that an unsalted short-query hash can be brute-forced and says what it would do (server-side salt or bucketed lengths only). |
| 5 | ANSWER.md | 10 | Full: success and stop criteria per rollout step (TTFT p95, completion rate, fallback rate, conversion and search exit compared to control), shadow cost estimate, server-side flag evaluation vs client, rollback path. Partial: generic. |
Total: 100
