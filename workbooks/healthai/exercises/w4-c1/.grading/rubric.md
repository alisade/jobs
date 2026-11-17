# Rubric: healthai/w4-c1 PA intake graph where no denial is ever automatic
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Safety by construction | 20 | Full: the auto path is a single positive condition (approve + threshold + all criteria met and cited + active coverage + nothing missing) and everything else falls through to review; `finalize` re-checks the invariant and raises; no code path lets model text set status. Partial: correct routing but finalize trusts the edges. Zero: deny/pend reachable without review. |
| 3 | Graph design and state | 15 | Clear nodes and conditional edges, reducers used correctly (audit append-only, no in-place mutation of state), reviewer validation loop via an edge rather than exceptions, Pydantic used for model output, resume value validated. |
| 4 | ANSWER.md | 15 | Explains the routing table, how the invariant is proven (exhaustive drive + finalize guard), and production concerns: Postgres checkpointer and thread ids, PHI inside checkpoints (encryption, retention, access), CMS-0057-F clock and specific denial reasons, threshold tuning from labelled cases. |
Total: 100
