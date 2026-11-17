# INC-48213: Q4 prior authorization metrics disagree with external audit

**Reported by:** Compliance (UM program integrity), 2026-11-24 08:12 ET
**Severity:** high (regulatory reporting)

The Q4 draft of our CMS-0057-F prior authorization metrics (impacted lines: Medicare Advantage,
Medicaid managed care, CHIP managed care) shows **0 late standard decisions**. The external auditor
pulled a sample of standard cases and says five of them were decided after the 7-day timeframe. Their
sample is attached (`audit_sample.csv`). The same deadline code drives the reviewer queue's "time
remaining" column, so if the report is wrong the queue is wrong too.

The analytics team says the report job logged a lot of DST warnings this run and asks whether the
November 1 time change broke the numbers.

We need: the real number of late standard decisions this quarter, the cause, a fix, and how we prevent a
repeat before the metrics are published.

Attachments: `report_run.log` (last run of `python -m clockreport.report`), `audit_sample.csv`.
