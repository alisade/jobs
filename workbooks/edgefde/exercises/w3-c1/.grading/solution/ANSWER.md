# ANSWER: edgefde/w3-c1 Champion/challenger promotion gate

## Approach

Wrote `decide` first as a pure function with unit tests, then `evaluate` against a stub model, then
`promote` around them, and the CLI last. Ran `make gate` for v1, v2, v3 in order.

## Fix

- Floors (recall >= 0.60, FAR <= 0.03, p95 <= 50 ms) stop a first model, or a champion-beating
  model, that is still unusable on the plant floor.
- Not worse on either metric stops the past failure: more recall bought with more false alarms (v3:
  0.755 recall, FAR 0.052 vs 0.021).
- Strictly better on one metric: a tie is churn on 10 gateways with no benefit and a rollout risk.
- Pinned holdout sha: both models are compared on exactly the data the team agreed on; a silently
  refreshed holdout fails closed instead of changing the bar.
- Fresh evaluation of champion and challenger: metrics stored in the registry may come from another
  holdout, another code version, or a failed job; the gate trusts only what it just computed, and
  logs it bound to the holdout hash.
- Every error exits 2 before any alias moves; `previous-champion` makes rollback one command.

## Trade-offs / what I would do in production

MLflow: `mlflow.register_model`, `MlflowClient.set_registered_model_alias`, `mlflow.evaluate` with the
pinned dataset, and a GitHub Actions job that posts `comment.md` on the PR and fails on exit 2/3.
With 278 fault windows a 0.01 recall gain is noise: add a bootstrap interval or a minimum margin, and
slice metrics per machine so one pump cannot hide behind the average. Before the alias moves on the
gateways, run the challenger in shadow mode for a week. The gate says nothing about drift after
promotion; that needs input and alert-rate monitoring.
