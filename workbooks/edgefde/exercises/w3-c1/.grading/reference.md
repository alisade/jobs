# Reference: edgefde/w3-c1

Reference implementation: `.grading/solution/gate/gate.py`.

- `evaluate` computes recall and false-alarm rate from `predict`, then times 200 single-row calls
  after 10 warm-ups and takes the 95th percentile. Thread pools are pinned to 1 in the tests: with
  oversubscribed OpenMP pools single-row latency of tree models is noise.
- `decide` collects reasons instead of returning early, so the PR comment lists every failed rule.
  Floors always apply; with a champion the challenger must be not worse on recall and false-alarm
  rate and strictly better on one. Ties are rejected.
- `promote` checks the pinned holdout hash first, refuses a challenger that is already champion,
  loads artifacts with errors mapped to `GateError`, evaluates both versions freshly, logs both
  metric sets bound to the holdout sha, decides, writes the comment, and only then moves aliases
  (`previous-champion` first, then `champion`).
- `rollback` moves `champion` back and deletes `previous-champion`.
- `main` maps `GateError`, `RegistryError`, `OSError`, `KeyError`, `ValueError` to exit 2.

Expected run: v1 recall 0.637 / FAR 0.025 promoted; v2 0.705 / 0.021 promoted; v3 0.755 / 0.052
rejected (above the 0.03 ceiling and worse than champion).

Interview angles: the holdout has 278 fault windows, so recall moves in steps of 0.0036 and a 0.01
difference is within noise; a production gate adds a bootstrap confidence interval or a minimum
margin, per-machine slices, and a shadow period on gateways before the alias moves. The gate cannot
see drift after promotion; that is monitoring's job.
