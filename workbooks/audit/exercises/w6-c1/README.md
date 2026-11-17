# audit/w6-c1 - Eval harness per control: accuracy, exception recall, consistency, cost and a CI gate

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 6 (Mon: error analysis and labeled sets; Tue: accuracy, recall, consistency; Wed: cost and latency; Thu: evals in CI)

## Scenario

The MFH audit committee will only let ControlPilot test CM-03 for the year-end SOX cycle if internal
audit can show, with numbers, how often the agent is right, whether it is consistent, what it costs
and that a prompt or model change cannot quietly make it worse. Two reviewers labeled 30 sampled
changes by hand (`data/labels.jsonl`, provenance in `labeled_by` / `labeled_at`). The agent (prompt
v3) was run 5 times per sample and every run was recorded with its outputs, token usage and latency
(`data/runs.jsonl`; one run timed out and is missing). A developer now proposes prompt v4, which is
shorter and cheaper (`data/runs_prompt_v4.jsonl`). Your harness decides whether v4 may ship.

The costly error in controls testing is a **missed exception**: a failed control reported as
effective. A false exception costs a reviewer ten minutes. The gate therefore keys on exception
recall first.

## What you have

| Path | What it is |
|---|---|
| `evalkit/metrics.py` | metric functions you write (helpers at the top are complete) |
| `evalkit/report.py` | `build_report` and `gate` you write; `to_markdown` is complete |
| `evalkit/cli.py`, `evalkit/data.py` | CLI and loaders (complete) |
| `data/labels.jsonl` | 30 human labels: four attributes plus `overall`, with provenance |
| `data/runs.jsonl`, `data/runs_prompt_v4.jsonl` | recorded runs: `outputs`, `overall`, `usage`, `latency_ms` |
| `data/prices.json` | USD per 1M tokens: input, cached_input, output (illustrative prices) |
| `baseline.json` | accepted v3 metrics and the thresholds agreed with the control owner |

Outcomes: attributes are `pass` / `exception` / `not_evaluable`; `overall` is `pass` / `exception` / `needs_review`.

## Your task

1. **Metrics** (`metrics.py`), exactly as defined here:
   - `accuracy(labels, runs, field)`: run-level. Over `scored_rows` (labeled samples, first row of
     each `(sample_id, run)`), the share whose value for `field` (an attribute or `"overall"`) equals
     the label. `None` when there are no scored rows.
   - `exception_scores(labels, runs, field)`: positive class `exception`, run-level over scored rows.
     Returns `tp, fp, fn, support (= tp + fn), recall, precision`; recall/precision are `None` when
     their denominator is 0 (a slice with no exceptions has undefined recall, not 0 and not 1).
   - `modal(values)`: `(value, count)` of the most frequent value; ties go to the more severe
     outcome (`SEVERITY`: exception, then needs_review/not_evaluable, then pass).
   - `agreement(runs, field="overall")`: per sample (all rows, labeled or not, duplicates dropped),
     modal count / runs present; return `mean_modal_agreement`, `fully_consistent_share` (samples
     whose runs all agree) and `samples`.
   - `fleiss_kappa(runs, field="overall", n_runs=5)`: Fleiss' kappa over samples that have exactly
     `n_runs` runs (runs are the raters); categories are the values observed. Return `kappa` and
     `subjects`; `kappa = 1.0` when expected agreement is 1; `None` when no subject qualifies.
   - `run_cost(row, prices)`: `((prompt - cached) * input + cached * cached_input + output * output) / 1e6`.
     `cost(runs, prices)`: `total_usd` over every row (every recorded run was billed),
     `per_100_samples_usd = 100 * total / rows`, `runs`.
   - `percentile(values, p)`: nearest rank, the sorted value at 1-based rank `ceil(p/100 * n)`;
     `None` for no values. `latency(runs)`: `p50_ms`, `p95_ms`, `runs`.
2. **Report** (`build_report`): keys `control`, `samples` (labeled), `runs_scored`, `missing_runs`
   (labeled samples x runs `1..expected_runs` not recorded, sorted by sample then run, as
   `{"sample_id", "run"}`), `unlabeled_samples` (sorted ids that have runs but no label),
   `accuracy` and `exceptions` for every field in `FIELDS`, `consistency` (`agreement`,
   `fleiss_kappa` on overall), `cost`, `latency`.
3. **Gate** (`gate(report, baseline_metrics, thresholds)`): a failure when overall exception recall
   is `None` or below `min_exception_recall`, and a failure when overall accuracy is below
   `accuracy_overall - max_accuracy_drop` (equal to the floor passes). Return readable reasons.
4. Run `make eval` and `make eval-v4`. In `ANSWER.md`: is v4 allowed to ship, with the numbers;
   what the v3 numbers say about S025 and S017; why run-level metrics and 5 runs; and what you would
   add before the audit committee relies on it (sample size of the eval set, confidence intervals,
   per-attribute gates, label quality).

## Acceptance criteria (what the grader checks)

- Every metric matches hand-computed values on small datasets, including ties, all-disagree,
  incomplete subjects, zero-exception slices, duplicates and unlabeled rows.
- Report keys and missing-run detection exactly as specified; the report is JSON-serializable.
- The gate passes v3 and blocks v4 through the CLI (exit code 1).
- ANSWER.md interprets the numbers for an audit manager, not only for an engineer.

## How to run

```bash
make setup      # shared venv
make test       # visible tests
make eval       # report for prompt v3 in out/v3/
make eval-v4    # report for the v4 candidate in out/v4/ (exit 1 means blocked)
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/w6-c1
make clean
```
