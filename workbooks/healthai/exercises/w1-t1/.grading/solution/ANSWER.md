# ANSWER: healthai/w1-t1 The CMS clock report says zero late decisions

## Approach

Recomputed the deadline for the five audit cases by hand, then diffed `decision_deadline` against a
plain "local wall clock + 7 days" for every standard case in the export.

## Root cause

`clockreport/deadlines.py`: `decision_deadline` calls `add_days(local, STANDARD_DAYS)`, and `add_days`
defaults to `business=True` (legacy toolkit API). Standard deadlines were 7 business days, i.e. 9 to 11
calendar days. Example: PA-2026-00201 and PA-2026-00419 were decided a day or more after the 7-day mark
but before the business-day deadline, so the report counted them on time. Before the fix: standard late
0/374. After: 21/374; expedited stays 7/111 (that path is 72 elapsed hours and never used add_days). All
five audit sample cases are late in the fixed report.

## Fix

`add_days(..., business=False)` in `decision_deadline` with a comment pointing to the rule. Verified with
`make report`, the audit sample, and tests for Friday and Saturday receipts and a fall-back crossing.

## Trade-offs / what I would do in production

The DST warnings are noise: the code keeps the local time of day by design. The real impact is the
reviewer queue, which showed extra days remaining; review recent standard cases for late decisions.
Make `business` keyword-only with no default, add rule-text table tests, have compliance sign the rule
interpretation, and recompute the metric independently before publishing.
