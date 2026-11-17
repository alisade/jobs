# Rubric: ms/w2-c2 Nightly orchestration pipeline with polling, fan-out and failure paths
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Failure semantics | 15 | Full: ANSWER explains why an Until timeout surfaces as Failed, why Fail activities (not just a red activity) set the run status, and why waitOnCompletion matters. Partial: implemented but not explained. Zero: failure paths missing or on Completed. |
| 3 | Policy and retry reasoning | 10 | Full: retry/timeout values justified per activity, idempotency of retried POST considered. Partial: values set with no reasoning. |
| 4 | Concurrency correctness | 10 | Full: no variables written inside the parallel ForEach, batchCount justified against capacity. Partial: correct but unexplained. Zero: Set variable in a parallel loop. |
| 5 | Trade-offs in ANSWER.md | 10 | Full: polling vs callback, testing and promotion approach, alert routing. Partial: one of these. |
Total: 100
