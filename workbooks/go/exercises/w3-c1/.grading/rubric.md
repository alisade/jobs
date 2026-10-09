# Rubric: go/w3-c1 A client-go config reloader: informers and a rate-limited work queue
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Controller pattern correctness | 20 | Full: handlers only enqueue keys; reconcile is level-based (reads cache, computes desired state, never trusts the event payload); Get/Done/Forget/AddRateLimited used correctly; WaitForCacheSync before workers; clean shutdown with a WaitGroup. Partial: works but does API calls in handlers, live GETs, or leaks the rate limiter. Zero: edge-triggered logic or no queue. |
| 3 | API write hygiene | 10 | Full: merge/strategic/apply patch touching only the one annotation; null to delete; no write when converged; errors aggregated per Deployment so one failure does not hide others. Partial: patch but writes every reconcile. Zero: Update with read-modify-write. |
| 4 | Go quality | 5 | Idiomatic: small functions, `errors.Join`, sorted keys via `slices.Sorted(maps.Keys(...))`, no shared mutable state outside the queue. |
| 5 | ANSWER.md and production judgement | 15 | Full: explains level vs edge triggering, why tombstones exist, the retry/drop policy choice, and 2-3 production points (an indexer keyed by referenced ConfigMap instead of List per reconcile, leader election for HA, Secrets support without logging values, metrics on queue depth/retries, rollout storms when a shared ConfigMap changes). Partial: generic. Zero: empty. |
Total: 100
