# ANSWER: edgefde/w3-t1 Model v7 promoted on a stale metric

## Approach

Read `ci-build-412.log` top to bottom, then compared the gate's numbers with the registry snapshot,
then the changelog against the alert counts.

## Root cause

A chain of three faults in CI plus a schema mismatch on the gateway:

```text
WARN evaluate: evaluation of v7 failed, continuing: KeyError('kurtosis_excess')
gate: challenger v7 recall=0.6888 far=0.0207 vs champion v6 recall=0.6888 far=0.0207
gate: PROMOTE v7 -> champion
[build #412] exit code 0
```

1. v7 was trained on feature schema v2 (`kurtosis` renamed to `kurtosis_excess`, changelog
   2026-10-28); the pinned holdout is schema v1, so evaluation raised KeyError.
2. `ci/evaluate.py` swallows every exception and returns 0: green build, and `versions/7.json` has
   `"metrics": []`.
3. `ci/gate.py` reads challenger metrics with `latest_metrics(name)`, which returned v6's metrics from
   its 2026-10-31 re-evaluation on the pinned holdout. The gate compared v6 with v6.
4. `>=` on both metrics turned the tie into a promotion.

On the gateways the adapter maps `kurtosis_excess` to the device's Pearson `kurtosis`, about 3 higher
than what v7 saw in training, on every window. `gateway-alerts.csv`: about 300 alerts/day with v6,
about 1,950/day with v7, confirmed faults flat at about 50/day: the extra alerts are false alarms.

Not the cause: the holdout refresh (done properly: sha re-pinned, v6 re-evaluated) and the pip cache
miss (slower install only).

## Fix

`ci/evaluate.py` returns 1 on any failure and logs nothing. `ci/gate.py` reads metrics with
`metrics_for(name, version, pinned_sha)` for both models, exits 2 if either is missing, and requires
not-worse on both metrics plus strictly better on one. `make run`: build fails at step 3, v6 stays
champion. `make test` passes.

## Trade-offs / what I would do in production

Now: move `champion` back to v6 (or run the rollback) and tell the planners why. Then: every model
version carries its input schema; CI checks it against the holdout and the gateway refuses a model
whose schema it does not emit, instead of aliasing features with different meaning. Shadow the
challenger on the gateways for a few days, and alarm on alerts per pump-day after any promotion with
an automatic rollback threshold.
