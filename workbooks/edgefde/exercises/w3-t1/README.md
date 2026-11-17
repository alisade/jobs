# edgefde/w3-t1 - Model v7 promoted on a stale metric

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 3 (Wed: eval gates in CI; Thu: monitoring and drift)

## Scenario

Monday 2026-11-09, Corvane Industrial's maintenance planners (fictional) to the reliability lead, who
forwards it to you:

> "The pump system cried wolf all weekend: about 1,950 alerts a day on 10 pumps instead of 300. Two
> planners drove in on Saturday for nothing. Nobody changed anything on the gateways. The nightly
> pipeline promoted a new model on Friday and the gate passed it, so the model should be fine?"

The nightly pipeline trains, registers, evaluates and gates `pump-anomaly`; the gate moves the
`champion` alias that the gateways pull. `make setup` rebuilds the registry exactly as it was before
build #412 and replays steps 3-4 of that build through the code in `ci/`, so the log in `incident/`
is the real output of the current code.

## What you have

| Path | What it is |
|---|---|
| `incident/ci-build-412.log` | output of build #412 |
| `incident/registry-snapshot/` | the registry after the build (version records, metrics, alias history) |
| `incident/gateway-alerts.csv` | alerts and confirmed faults per day across the 10 pumps |
| `incident/changelog.md` | the team's changelog for the period |
| `ci/evaluate.py`, `ci/gate.py`, `ci/pipeline.sh` | CI steps 3 and 4 (edit) |
| `mlreg/` | the file-based registry (`metrics_for`, `latest_metrics`, aliases) and model wrapper (do not edit) |
| `scripts/` | the incident builder and data generator (do not edit) |
| `data/` | the registry and holdout after the replay |

## Your task

1. Find why v7 was promoted and prove it from the incident files: what did the gate actually compare?
2. Explain why the gateways raised six times more alerts with v7 (the model itself is not bad).
3. Decide whether the holdout refresh and the cache warning matter.
4. Fix `ci/` so that an unevaluated or wrongly evaluated challenger can never be promoted: the build
   must go red, the champion must stay where it is, and a genuinely better, properly evaluated
   challenger must still be promoted.
5. Write the immediate remediation for the plant and the prevention list.

## Acceptance criteria (what the grader checks)

- Replaying build #412 (`make run`): the pipeline exits non-zero and v6 stays champion.
- `ci.evaluate` exits non-zero when evaluation fails and logs nothing.
- `ci.gate` exits 2 when the challenger has no metrics for **its own version on the pinned holdout**,
  or when the champion has none; 0 for a strictly better challenger (and sets `previous-champion`);
  3 for a tie or a worse challenger.
- `ANSWER.md`: the full chain of causes with quoted evidence, the red herrings, remediation and
  prevention.

## How to run

```bash
make setup     # venv, data/, incident/
make run       # replay build #412 through your current ci/ code (fresh copy in run/)
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/w3-t1
make clean
```

## What to submit

Your changes under `ci/` and a filled-in `ANSWER.md`.
