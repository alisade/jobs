# Rubric: edgefde/w5-c1 OTA model rollout with canary and automatic rollback
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | State machine and resume | 15 | Explicit persisted state (phase, touched, skipped, streaks, offline counters), atomic writes, resume continues the same rollout, start refuses while one is active. Partial: resume restarts from scratch or state is written non-atomically. |
| 3 | Gates and rollback | 15 | Every touched device is gated every window (not only the current batch), rollback covers all touched devices including those currently offline, the reason names device and gate, rollback waits for convergence. |
| 4 | Offline handling | 5 | Offline is not failure; timeout then skip back to the known-good version; reported. |
| 5 | Production mapping | 15 | ANSWER.md maps to AWS IoT Jobs (rollout config, abort config on failure thresholds), Greengrass deployments or Mender; canary per hardware revision (rev2 was the real risk); model metrics vs confirmed outcomes; alerting on rollback. |
Total: 100
