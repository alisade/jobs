# Business calendar

- Customer quarter-end reporting: last 5 business days of each quarter, plus the first 2 business
  days of the next. RIQ traffic 3x normal. Change freeze for prod (exceptions: security fixes with
  CAB approval).
- Black Friday to Cyber Monday (2026-11-27 to 2026-11-30): retail customers, RDM traffic 2.5x.
  Freeze.
- Year-end freeze: 2026-12-18 to 2027-01-04.
- Normal change windows: Tue-Thu 14:00-20:00 UTC (staffed by the platform team), Sat 06:00-12:00 UTC
  only with an engineer on the bridge.

# SLOs (prod, per service, 28-day window)

| Service | Availability SLO | Latency SLO | Error budget per 28 days |
|---|---|---|---|
| RIQ API | 99.95% | p95 < 300 ms | ~20 min |
| MDM API | 99.9% | p95 < 500 ms | ~40 min |
| RDM API | 99.9% | p95 < 200 ms | ~40 min |
| mdm-search | 99.5% (internal) | - | ~3.4 h |

On-call: 12-hour rotations (08:00-20:00 and 20:00-08:00 UTC), one primary, one secondary.
