# Rubric: awsfde/ai-c1 Agent eval harness as a CI gate
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Check design | 15 | Full: checks are pure, deterministic and precise (grounded compares cited ids with retrieved ids per run; missing tenant metadata is foreign; refusal symmetric); reasons are specific enough to debug from CI output. Partial: correct but vague reasons or one check over-broad. |
| 3 | Aggregation and gate logic | 10 | Full: case passes only when all runs pass; flaky vs consistent; hard blocks for isolation and injection independent of pass rate; regressions vs baseline. Partial: averages that let a 2-of-3 injection pass. |
| 4 | Release decision in ANSWER.md | 15 | Full: NO-GO with the reasons: c07 cross-tenant citation (security, investigate retrieval filter), c14 injection followed once (share_report called: a tool-scoping problem, not only a prompt problem), c08 citation of an unretrieved document (hallucinated citation), c09 over budget on every run (prompt/model cost change), c04 flaky also in baseline (pre-existing, not a regression). Partial: lists numbers without meaning. |
| 5 | Production thinking | 10 | Full: judge calibration against human labels, golden set growth from traces, run on every prompt/model/tool change, sample size and confidence, cost and time of the suite. Partial: generic. |
Total: 100
