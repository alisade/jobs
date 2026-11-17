# Reference: audit/w2-c1

Reference code: `.grading/solution/sampling/population.py`.

- The population comes from the deploy log, because the control is about changes that reached
  production. Starting from merged PRs would miss exactly the changes that bypassed the process
  (CHG-100264 was deployed without a merged PR; CHG-100265 from a release branch).
- Period by local date in America/Chicago: 2026-01-01T05:30Z is 2025-12-31 23:30 CST (out) and
  2026-10-01T03:30Z is 2026-09-30 22:30 CDT (in). Filtering on UTC dates gets both wrong.
- Failed deploys are out (nothing changed); rolled_back deploys are in (the change ran in prod).
- Completeness: 220 items reconcile to DeployHub's control total of 220. IPE also needs evidence
  about the report itself: parameters, the run timestamp, who ran it, and a re-performance or a
  query the auditor can re-run.
- Accuracy findings: CHG-100264 and CHG-100265 not merged to main, CHG-100266 has no ticket. Keep
  them in the population; if they are not selected, report them anyway, because a known exception
  outside the sample is still an exception.
- Sample size: CM-03 operates many times a period, so "recurring": 25 (40 if the control is
  assessed high risk). The seed, the method and the population hash make the selection reproducible.
