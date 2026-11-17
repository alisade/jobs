# edgefde/w3-c1 - Champion/challenger promotion gate

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 3 (Tue: registry, versions and aliases; Wed: CI for models and eval gates)

## Scenario

Corvane Industrial's reliability team (fictional) retrains the pump anomaly model every two weeks.
Until now someone looked at a notebook and moved the "champion" alias by hand; twice that put a
model on the gateways that raised more false alarms than the one it replaced, and the maintenance
planners stopped trusting the alerts. You are asked to replace the human step with a CI gate that the
training pipeline calls after it registers a new version.

The registry is a small file-based fake with the same shape as the MLflow Model Registry
(`mlreg/registry.py`, complete): versions with lineage (run id, artifact, training-data hash), aliases
as mutable pointers (`champion`, `previous-champion`), alias history, and append-only metrics that
record which holdout set they were computed on.

`make setup` trains three versions of `pump-anomaly` on synthetic feature windows and registers them
(no aliases yet):

| version | model | what to expect |
|---|---|---|
| v1 | logistic regression, threshold 0.5 | the baseline |
| v2 | gradient-boosted trees, threshold 0.5 | higher recall and fewer false alarms than v1 |
| v3 | the same trees, threshold 0.1 | higher recall, but false alarms more than double |

## What you have

| Path | What it is |
|---|---|
| `mlreg/registry.py` | file-based registry (do not edit) |
| `mlreg/wrappers.py` | the pickled model wrapper (`predict(X) -> 0/1`) (do not edit) |
| `gate/gate.py` | the gate (TODO) |
| `scripts/data.py` | builds `data/`: `train.npz`, `holdout.npz`, `models/v*.pkl`, `registry/` |

## Your task

Implement `gate/gate.py`:

- `holdout_sha(path)`: sha256 hex of the holdout file.
- `evaluate(model, X, y, latency_samples=200) -> Metrics`: recall = detected fault windows / fault
  windows; false-alarm rate = alerts on healthy windows / healthy windows; p95 latency in ms of
  `predict` on single rows (batch size 1, after a few warm-up calls); counts of positives and negatives.
  A holdout without both classes is a `GateError`.
- `decide(champion, challenger, rules) -> Decision(promote, reasons)`:
  - the challenger must always meet the absolute floors in `Rules` (recall >= 0.60, false-alarm rate
    <= 0.03, p95 <= 50 ms);
  - with a champion: recall not lower, false-alarm rate not higher, and strictly better on at least
    one of them (a tie is not a reason to change what runs on 10 pumps);
  - without a champion (first model): the floors decide;
  - `reasons` says why, in words a reviewer can read.
- `promote(registry, name, challenger, holdout, expected_sha, rules, comment_path) -> int`:
  - fail closed (`GateError`) if the holdout's sha256 is not the pinned `expected_sha`, if the
    challenger is already champion, or if any artifact cannot be loaded;
  - evaluate the challenger **and** the current champion freshly on the same holdout; never trust
    metrics already in the registry; log both with `registry.log_metrics(..., holdout_sha, ...)`;
  - on promote: `previous-champion` -> old champion (if any), `champion` -> challenger; return 0;
    on reject: aliases untouched, return 3;
  - write a markdown PR comment to `comment_path` when given: a table with a `| recall |` row,
    false-alarm rate and p95 for both versions, and a line `Decision: PROMOTE` or `Decision: REJECT`
    followed by the reasons.
- `rollback(registry, name)`: `champion` back to `previous-champion` and drop that alias; `GateError`
  when there is nothing to roll back to.
- `main(argv)`: subcommands `promote` and `rollback` (flags in the module docstring); exit 0 promoted
  or rolled back, 3 rejected, 2 on any error (message on stderr).

## Acceptance criteria (what the grader checks)

- v1 first: promoted. Then v2: promoted, `previous-champion` = v1. Then v3: rejected with reasons.
- Ties rejected; floors and the latency budget applied; stale or fake metrics in the registry ignored.
- Hash mismatch and unreadable artifacts fail closed and change no alias.
- Rollback works once and then errors; CLI exit codes 0 / 3 / 2.
- `ANSWER.md`: why each rule exists, and what this gate still cannot catch.

## How to run

```bash
make setup
make gate V=1   # then V=2, then V=3; prints the PR comment and the exit code
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade edgefde/w3-c1
make clean
```

## What to submit

`gate/gate.py` and a filled-in `ANSWER.md`.
