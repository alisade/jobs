# audit/w6-t1 - "97% accuracy" on the dashboard, 4 missed exceptions in review

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 6 (Mon: error analysis and labeled sets; Thu: evals in CI)

## Symptoms

The MFH IT audit senior re-performed all 30 items of the Q3 2026 CM-03 sample before sign-off.
ControlPilot reported 3 exceptions; the reviewer found 7. The four the agent called "pass" are listed
in `incident/reviewer-memo.md`. At the October steering committee the eval dashboard showed
**96.7% accuracy and 100% exception recall**, and it still does (`make dashboard`). The audit
manager wants to know how both can be true, whether any other result from the harness can be
trusted, and what stops it from happening again before the year-end cycle.

Finance has also asked why the dashboard shows $84 per 100 samples when the October invoice for
all of ControlPilot is $3.12 (`incident/finance-note.txt`).

## What you have

| Path | What it is |
|---|---|
| `harness/` | the dashboard harness: golden loader, scoring, CLI |
| `scripts/refresh_golden.py` | the script behind `make refresh-golden` |
| `labels/golden.jsonl` | the golden set the dashboard scores against |
| `labels/human_v1/` | the reviewer-signed labels from July (do not edit) |
| `runs/2026Q3/production.jsonl` | the Q3 production run that was reported |
| `runs/replay-2026-10-30.jsonl` | a replay of the Q3 sample with prompt v3.2 |
| `config/prices.json` | price table used by the dashboard |
| `incident/` | written by `make setup`: reviewer memo, dashboard snapshot, repo history, refresh log, finance note |

## Your task

1. Find out why the dashboard disagrees with the reviewer. Write the root cause in `ANSWER.md`
   with evidence (file contents, command output, dates from the history).
2. Restore trustworthy ground truth and re-score Q3. Report the true accuracy, exception recall and
   the missed exceptions.
3. Make the failure impossible to repeat silently: the harness must refuse to score against golden
   rows that a human did not label (`harness.golden.ProvenanceError`, a `ValueError`), and
   `make refresh-golden` must never produce model-labeled ground truth (migrate the schema in place
   from human labels, or refuse).
4. Decide whether the finance question is the same problem. Fix it or explain it.

## Acceptance criteria (what the grader checks)

- `labels/golden.jsonl` holds the human labels (labels, overall, labeled_by, labeled_at unchanged)
  in the schema v2 shape (`control_id` present); `labels/human_v1/` unchanged.
- Scoring Q3 against it reports the reviewer's numbers.
- `load_golden` raises `ProvenanceError` for any row whose `labeled_by` does not start with
  `human:`, and still enforces schema v2; the CLI exits non-zero on such a file.
- `scripts/refresh_golden.py` run on the fixed repo leaves the labels as they are, and given a file
  with a model-labeled row it refuses (non-zero exit) instead of writing it as ground truth.
- `ANSWER.md`: root cause with evidence, the true numbers, why the old numbers looked good, the
  secondary finding, and the process change.

## How to run

```bash
make setup           # shared venv + incident/ bundle
make dashboard       # what the steering committee saw
make test            # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/w6-t1
make clean
```
