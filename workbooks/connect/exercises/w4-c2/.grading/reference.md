# Reference: connect/w4-c2

Model answer: `.grading/solution/DESIGN.md`. What great looks like:

- Dates drive the plan: Five9 renewal 2027-01-31 cannot be met for overflow inbound, so the plan
  says so and negotiates a short extension instead of pretending; wave 2 lands after the
  year-end blackout and before the Avaya renewal, with a fallback.
- A pilot wave with real porting (low-volume outage line) proves carriers, LOAs and the runbook.
- Coexistence is explicit (AWS Avaya-to-Connect Prescriptive Guidance has three options); context
  across platforms is handled through ServiceNow rather than assuming UUI/X- headers reach Connect.
- Rollback accepts that number ports are effectively one-way in the short term, so rollback means
  routing back to Avaya through DIDs still on Avaya, re-publishing flow versions, module aliases
  and feature flags.
- The factory rationalises before translating (low-volume vectors retired), has golden path
  suites per script, and a definition of done.
- Offshore model: RACI, overlap hours, design/PR review cadence, ADRs.
- Decommission includes recording retention (Object Lock/Glacier) and licences kept through
  hypercare.
