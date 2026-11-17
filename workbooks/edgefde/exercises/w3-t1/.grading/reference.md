# Reference: edgefde/w3-t1

## Cause chain

1. On 2026-10-28 the feature store moved to schema v2: `kurtosis` became `kurtosis_excess` (excess
   kurtosis, Gaussian = 0). Build #412 trained v7 on schema v2. The pinned holdout is still schema v1,
   so evaluating v7 raises `KeyError('kurtosis_excess')`.
2. `ci/evaluate.py` catches every exception, prints a WARN and returns 0. The build stays green and v7
   has no metrics (`registry-snapshot/models/pump-anomaly/versions/7.json`: `"metrics": []`).
3. `ci/gate.py` reads the challenger's numbers with `latest_metrics(name)`: the most recent metrics of
   ANY version. That is v6's re-evaluation on the refreshed holdout (2026-10-31). The log line shows
   v7 and v6 with identical recall and false-alarm rate.
4. The comparison uses `>=` on both metrics, so the tie promotes. v7 becomes champion untested.
5. On the gateways the adapter alias table maps `kurtosis_excess` to the device's Pearson `kurtosis`
   field, so v7 sees every window about 3 units more impulsive than in training: about 1,950 alerts/day
   instead of about 300, with confirmed faults unchanged (about 50/day).

Red herrings: the holdout refresh was handled correctly (new sha pinned, champion re-evaluated). The
cache miss slowed the install only.

## Fix

`.grading/solution/ci/evaluate.py` returns 1 on any evaluation error and logs nothing.
`.grading/solution/ci/gate.py` uses `metrics_for(name, version, pinned_sha)` for both challenger and
champion, exits 2 when either is missing, and promotes only when not worse on both and strictly
better on one.

## Remediation and prevention

Roll `champion` back to v6 now (the gateways pull the alias), tell the planners. Then: a declared input
schema in every model version, checked in CI against the holdout and checked by the gateway before it
loads a model (no silent alias mapping between features with different semantics); shadow mode before
promotion; alert-rate per pump-day monitored after promotion with an automatic rollback threshold.
