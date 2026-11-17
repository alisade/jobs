# PAGE: criteria-service SLO burn (prod), 2026-11-18 09:14 ET

**From:** Cloud Monitoring alert policy `criteria-service availability < 99%` (fast burn)
**Also reported by:** UM reviewer support desk: "Case status pages spin and then say 'criteria check
unavailable'. Started a bit after 9. Nurses cannot see criteria results for any case."

Timeline from the on-call channel:
- 09:10 Healthcare API FHIR store latency alert fired (search p95 2.8 s); it cleared at 09:14.
- 09:14 criteria-service availability alert fired. Every CheckCriteria call from the edge ends in
  DEADLINE_EXCEEDED after 1 s. Health RPC still returns SERVING, so Cloud Run keeps the revision.
- 09:31 still failing although the FHIR store is healthy. CPU on the revision is near 0.
- 09:40 someone restarted the revision (deployed the same image); everything recovered at once.

Ask: why did the service stay down after the FHIR store recovered, and why did a restart fix it?
Find the cause before the next FHIR blip does it again. Attached: `criteria-service.log`,
`fhir-latency.csv`. `make repro` replays the morning against a fake FHIR store.
