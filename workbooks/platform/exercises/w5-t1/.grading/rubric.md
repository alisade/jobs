# Rubric: platform/w5-t1 The RIQ burn-rate alert never fired
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: PLAT-1199 (2026-10-20) replaced the ServiceMonitor, whose `targetLabels: [service]` copied the Service's `service` label onto every series, with a PodMonitoring; managed collection attaches project_id, location, cluster, namespace, job (the PodMonitoring name) and instance but no `service`. The recording rules still aggregate `sum by (service, code)`, so their output has no service label (`{code="503"}`, ratio `{}`), and the alerts select `{service="riq-api"}`, which matches nothing: the expression is an empty vector, never an error, so the evaluator logs "evaluated" and nothing fires. PLAT-1199's "expressions unchanged" is the trap. Partial (10-15): "label mismatch" without the scrape config change or without explaining why there were no errors. Zero: blames Alertmanager or the silence. |
| 3 | Evidence | 20 | Full: at least three of: query output showing raw series labels without `service`; the recording rule expr returning `{code=...}` / `{}` at 13:30 with a ratio above 0.0144; the alert expr returning an empty vector; the ServiceMonitor targetLabels vs PodMonitoring diff; the git log; `make alerts` output before and after. Partial: one or two. Zero: assertion only. |
| 4 | Red herrings | 10 | Rules out the canary silence (expired 2026-11-03 21:00, before the outage) and the Alertmanager route (a `continue: true` route still delivers to pagerduty-core-services; no alert ever reached Alertmanager: the evaluator shows alerts_active=0). |
| 5 | Fix quality | 10 | Aggregates by job, namespace (and cluster, or argues for fleet-wide aggregation with the dilution trade-off), selects job="riq-api" and namespace="riq", keeps the 14.4/6 thresholds and windows for 99.9%, adds an `absent()` style guard at a non-paging severity (or argues for paging) with a `for:`. |
| 6 | Production follow-ups | 5 | Concrete: rule unit tests in CI with fixture series (promtool test rules style), a label contract for PodMonitoring/ClusterPodMonitoring, a per-SLO guard, a synthetic error-injection test each quarter, migration checklists that diff rule results before and after. |
Total: 100
