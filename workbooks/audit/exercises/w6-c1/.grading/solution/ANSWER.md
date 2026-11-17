# ANSWER: audit/w6-c1 Eval harness per control

## Approach

Implemented each metric as a pure function and checked it against small hand-computed sets first
(ties, all-disagree, incomplete subjects, empty slices), then ran it on the committed data. Undefined
values are None: a recall of 0 or 1 on a slice with no exceptions would be a false statement.

## Fix

metrics.py: run-level accuracy and exception scores over labeled, de-duplicated rows; modal with a
severity tie-break; agreement; Fleiss kappa over complete subjects; cost with cached tokens at the
cached price; nearest-rank percentiles. report.py: build_report with missing and unlabeled lists,
gate on exception recall and on accuracy drop.

v3: accuracy 0.960, overall exception recall 29/30, kappa 0.816, about $0.087 per 100 samples,
p95 8.4 s; gate passes. v4: accuracy 0.900, recall 20/30; independent_approver recall drops to 3/15
because v4 stops resolving e-mail aliases, so self-approvals on S004 and S027 pass in every run (S013 stays an exception through approval timing). v4 is
blocked; being cheaper does not offset a missed SoD exception.

S025 is a needs_review sample answered pass in 2 of 5 runs: an inconsistency that hides an unresolved
identity. S017 run 5 is missing (timeout) and is reported as a gap.

## Trade-offs / what I would do in production

30 samples with 7 distinct exceptions gives wide intervals (Wilson 95% on 29/30 is about 0.83-0.99).
Add labeled exceptions, gate per attribute, check reviewer agreement on labels, run the gate in CI on
every prompt, model or config change, update the baseline only with control-owner sign-off and keep
each report as evidence for the release.
