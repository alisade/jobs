# Rubric: healthai/w4-t1 A reviewer's decision lands on another member's case
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause and evidence | 40 | Full: PA-2290 introduced the module-level `RUN_CONFIG` dict; `submit_decision` writes the thread id into it, then awaits the audit write, then resumes with the shared dict, so the last coroutine to set it wins and every resume goes to that thread (PA-2026-0008 in the replay). Evidence: repro output and audit lines showing receipts for three cases and determinations only on 0008. Partial: shared state named without the await/interleaving mechanism. Zero: thread-id scheme or checkpointer blamed. |
| 3 | Fix and guard | 15 | Config built per call (no shared mutable state), a check that the determination's case id equals the requested one, tests that run bursts with several interleavings. |
| 4 | Privacy and repair | 15 | Identifies what crossed (another reviewer's decision and reason on case 0008's thread; the other cases still waiting), proposes repairing 0008 by forking from the checkpoint before the bad resumes (time travel) and re-queuing 0002 and 0003, and adds idempotency keys plus a concurrency test in CI. |
Total: 100
