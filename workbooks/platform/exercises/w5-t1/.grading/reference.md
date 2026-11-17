# Reference: platform/w5-t1

Fixed rule file: `.grading/solution/rules/riq-slo.rules.yaml`.

## Root cause

PLAT-1199 (c2f9e10, 2026-10-20) moved scraping from kube-prometheus-stack to managed collection. The
old ServiceMonitor had `targetLabels: [service]`, which copies the Service's `service: riq-api` label
onto every scraped series. The new PodMonitoring attaches the managed-collection target labels
(project_id, location, cluster, namespace, job = PodMonitoring name, instance) and nothing else. 5e07b44
ported the SLO rules "expressions unchanged":

- recording rules `sum by (service, code) (...)`: `service` is missing, so output is `{code="200"}`,
  `{code="404"}`, `{code="503"}`; at 13:30 the 5m rate of 503s is about 7.4 req/s of 121;
- ratio rules `sum by (service) (...)`: output `{}`; the 1h ratio at 13:30 is about 0.0188, well above 0.0144;
- alerts select `{service="riq-api"}`: an empty vector. Empty is a valid result, so the rule evaluator
  logs "rule group evaluated ... alerts_active=0" with no error.

## Red herrings

- Silence 7f1c2a9e covered RiqApi.* on prod-blue but expired 2026-11-03 21:00, 16 hours before the outage.
- The PLAT-1231 route with `continue: true` sends matching pages to pagerduty-core-services and then also
  evaluates the next route; it cannot drop an alert. Nothing reached Alertmanager in the first place.

## Fix

Aggregate by `job, namespace, cluster, code` and select `job="riq-api", namespace="riq"`. Keeping
`cluster` pages for a single bad cluster at full strength: on a 50/50 fleet a fleet-wide ratio halves
the burn and delays the page (about 31 minutes instead of 16 in the two-cluster scenario). Add
`absent(job_code:http_requests:rate5m{job="riq-api", namespace="riq"})` with `for: 10m` at ticket
severity owned by platform.

Replay on the incident data: fast burn active 13:26, fired 13:28; slow burn fired 14:01.

## Follow-ups

Rule unit tests in CI with fixture series; a label contract per PodMonitoring; guard per SLO; a
migration checklist that compares recording rule output before and after; quarterly synthetic burn test.
