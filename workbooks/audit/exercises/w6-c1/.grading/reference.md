# Reference: audit/w6-c1

Reference code: `.grading/solution/evalkit/metrics.py` and `report.py`.

Numbers on the committed data:

| | prompt v3 | prompt v4 |
|---|---|---|
| overall accuracy (run-level) | 143/149 = 0.960 | 135/150 = 0.900 |
| overall exception recall | 29/30 = 0.967 | 20/30 = 0.667 |
| independent_approver recall | 14/15 | 3/15 |
| mean modal agreement / Fleiss kappa | 0.960 / 0.816 (29 complete samples) | 1.000 / 1.000 |
| cost per 100 samples | about $0.087 | about $0.075 |

v4 is blocked twice: recall 0.667 < 0.95 and accuracy 0.90 < 0.966 - 0.02. The misses are all on
`independent_approver`: v4 no longer resolves e-mail aliases, so self-approvals (S004 and S027 in every run, plus two runs
of S013, which stays an exception overall through approval timing) are reported as effective. This is exactly the costly error. The cost saving is irrelevant
against a missed SoD exception.

v3 observations: S027 run 2 missed the exception (the single FN); S025 is a needs_review sample
(unknown approver identity) that v3 answered pass in 2 of 5 runs, which inflates accuracy and is
invisible in a single-run eval; S017 run 5 is missing (timed out) and must be reported, not dropped.

Definitions worth defending: run-level metrics count every run because production uses one run per
sample; recall of a slice with no exceptions is undefined (None) and the gate treats undefined
recall as a failure, since you cannot claim the agent finds exceptions with no exceptions in the set.

Statistical honesty: with 30 positive run-rows from only 7 distinct exception samples, a Wilson
95% interval on 29/30 is roughly 0.83-0.99. Before reliance: more labeled exceptions (seed known
failures), per-attribute recall gates, a reviewer-agreement check on the labels, and the report filed
as evidence with the release.

Note that v4 is perfectly consistent (kappa 1.0) and still wrong: consistency measures whether the
agent repeats itself, not whether it is right. Report both, gate on recall.
