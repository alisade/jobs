# audit/w2-c1 - CM-03 population, completeness and accuracy checks, and a reproducible sample

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 2 (Wed: population completeness and accuracy; Thu: sampling)

## Scenario

Before ControlPilot tests a single change, someone has to define the population and prove it is
complete and accurate. At Meridian Freight Holdings (fictional) the external auditor reviews this
step first: if the population is wrong, every sample conclusion is worthless. This part stays
deterministic. No model is involved, and the selection must be reproducible a year from now by
someone who only has the workpaper.

Control CM-03 (program change) for the 2026 interim period: **every production change deployed
between 2026-01-01 and 2026-09-30, by local date in America/Chicago** (MFH's entity time zone).

## What you have

| Path | What it is |
|---|---|
| `exports/prs.json` | pull requests exported from source control (UTC timestamps) |
| `exports/deploys.csv` | DeployHub deployment log: every run to every environment, any status |
| `exports/tickets.csv` | change tickets (change_id, state, risk) |
| `exports/control_total.json` | DeployHub's own count of production changes for the period (the control total you reconcile to) |
| `exports/sampling_table.json` | MFH internal audit's sample size table by control frequency and risk |
| `sampling/exports.py` | loaders (complete) |
| `sampling/population.py` | what you write |
| `select.py` | `make select` runs the whole step and writes `selection_log.json` |

## Your task

1. `build_population()`: one item per change id with at least one prod deployment whose status is
   `succeeded` or `rolled_back` and whose local date (entity time zone) is in the period, inclusive.
   Re-deploys of the same change collapse to one item (first deployment, count kept). Join the PR;
   a change without a PR merged to `main` **stays in the population** with `pr_merged_to_main=False`
   (that is something to test, not a reason to drop it). Sorted by change_id.
2. `completeness()` reconciles the population count to the control total. `accuracy_checks()`
   returns one message per issue: no change ticket, PR missing from the export, PR references a
   different change, PR not merged to main, PR merged after the deploy. Each message starts with
   the change id.
3. `sample_size()` reads the table by frequency and risk (`standard` / `high`); unknown values raise
   `ValueError`.
4. `select_sample()`: sort the population by change_id, then `random.Random(seed).sample` over the
   indexes; return the items in selection order. If `n` is at least the population size, return
   everything. `population_hash()`: SHA-256 hex of the sorted change ids joined by newlines.
5. `selection_log()`: a JSON-serializable dict with control, method, seed, frequency, risk,
   sample_size, population_count, population_sha256, completeness (as a dict), accuracy_issues and
   selected ids.
6. `ANSWER.md`: how you would show the auditor that the population is complete and accurate (the
   IPE argument), what CM-03's frequency is and why, and what you do with the accuracy findings.

## Acceptance criteria (what the grader checks)

- Time-zone boundaries on both period ends; status and environment filters; re-deploys collapsed.
- Unmerged and off-main changes kept and flagged; population reconciles to the control total.
- All three seeded accuracy findings reported; merged-after-deploy detected.
- Sample size table lookups and errors; selection reproducible, order independent and exactly the
  documented method; selection log complete; `select.py` runs.

## How to run

```bash
make setup
make test
make select SEED=20261005
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/w2-c1
make clean
```
