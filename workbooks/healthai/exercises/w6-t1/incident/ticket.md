# SEC-342: member identifiers in exported traces and logs despite redaction

**Reported by:** Information Security, 2026-11-20
**Severity:** high (possible PHI disclosure to a vendor outside the BAA)

Our weekly scan of what the PA assistant exports found member names and member ids in about 3% of the
trace spans sent to the tracing vendor and in a sample of application log lines. Redaction is enabled
on both log handlers (SEC-311) and the span exporter scrubs attributes, so "this should not be possible".
The platform team thinks the exporter's nested-attribute TODO in `app/tracing.py` is the gap.

Exports to the vendor are paused. We need the root cause, a fix, evidence that it holds for every way
the code logs, and an assessment of what was exposed. `make setup` re-runs the pipeline against 300
synthetic cases and the scanner (`incident/scan_report.txt`).
