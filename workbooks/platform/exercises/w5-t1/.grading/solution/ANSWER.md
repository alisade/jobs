# ANSWER: platform/w5-t1 The RIQ burn-rate alert never fired

## Approach

Replayed the rules (`make alerts`: "no alerts fired"), then queried each layer at 13:30: raw series,
the recording rule exprs, the ratio exprs, the alert exprs. Then compared the scrape config before
and after PLAT-1199 and checked the silence and the route.

## Root cause

The SLO alerts select a label that no longer exists. PLAT-1199 (c2f9e10, 2026-10-20) replaced the
ServiceMonitor, whose `targetLabels: [service]` copied `service: riq-api` from the Service onto every
series, with a PodMonitoring. Managed collection attaches project_id, location, cluster, namespace, job
and instance only:

```
make query Q='count by (job, namespace, cluster) (http_requests_total)'
{"cluster": "prod-blue", "job": "riq-api", "namespace": "riq"} 9
```

The rules were ported "expressions unchanged" (5e07b44). `sum by (service, code)` now yields only `code`:

```
make query Q='sum by (service, code) (rate(http_requests_total{namespace="riq"}[5m]))'
{"code": "200"} 110.569
{"code": "404"} 3.43222
{"code": "503"} 7.43185
```

and the 1h ratio is `{} 0.0187546`, above the 0.0144 threshold, but the alert selects
`{service="riq-api"}`, which matches nothing. An empty vector is a valid result, so the evaluator log
shows "rule group evaluated ... alerts_active=0" and no error.

## Fix

Recording rules aggregate `by (job, namespace, cluster, code)` and select `job="riq-api",
namespace="riq"`; ratios by `(job, namespace, cluster)`; alerts select the same. Per cluster, because an
outage on one of two clusters would otherwise be diluted by half and page late. Added
`RiqApiSLOSeriesMissing`: `absent(job_code:http_requests:rate5m{job="riq-api", namespace="riq"})`, for 10m,
severity ticket, team platform. Verified with `make alerts RULES=...`: fast burn fired 13:28, slow burn
14:01; `make test` passes.

## Trade-offs / what I would do in production

Red herrings: the canary silence expired 2026-11-03 21:00, before the outage; the `continue: true`
route still delivers to pagerduty-core-services and nothing reached Alertmanager anyway (alerts_active=0).
Follow-ups: rule unit tests in CI with fixture series, run on every rule or scrape change; a label
contract for PodMonitoring; a guard alert per SLO; a migration checklist that diffs recording rule
output before and after; a quarterly synthetic burn test to prove the page path end to end.
