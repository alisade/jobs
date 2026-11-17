# Rubric: edgefde/w3-t1 Model v7 promoted on a stale metric
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause chain | 25 | Full: (a) evaluate.py swallowed KeyError('kurtosis_excess') and returned 0 (v7 trained on feature schema v2, holdout still schema v1), so the build stayed green and v7 has no metrics; (b) gate.py took `latest_metrics(name)`, which returned v6's 2026-10-31 re-evaluation, so it compared v6 with itself; (c) `>=` on both metrics made the tie a promotion. Partial: one or two links. Zero: "the model is bad". |
| 3 | Evidence | 10 | Quotes the WARN line, the identical recall/far numbers for v7 and v6 in the gate line, the empty `metrics` list in versions/7.json and the latest metrics entry being v6's on the pinned sha. |
| 4 | Gateway behaviour | 10 | Explains the six-fold alerts: the edge adapter maps `kurtosis_excess` to the gateway's Pearson `kurtosis` field, so v7 sees values about 3 higher than in training on every window; confirmed faults unchanged (about 50/day), so it is false alarms. |
| 5 | Red herrings | 5 | Holdout refresh was done properly (pinned sha updated, v6 re-evaluated on it); the cache miss only slowed the install. |
| 6 | Fix and prevention | 20 | Evaluate exits non-zero; gate binds metrics to (version, pinned holdout sha) and fails closed, keeps strict improvement; remediation: roll champion back to v6 now (with the planners told), then a feature-schema contract checked in CI and on the gateway (refuse to load a model whose input schema the device does not emit), shadow mode, alert-rate monitoring with a rollback trigger. |
Total: 100
