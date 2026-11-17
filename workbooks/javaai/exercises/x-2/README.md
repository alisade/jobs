# javaai/x-2 - When will the tutor portfolio be done? Flow metrics and a Monte Carlo forecast

**Type:** coding | **Estimate:** 1.5-2 hours | **Study plan:** Week 7 add-on (Thu: Kanban, flow metrics and forecasting)

## Scenario

The Kestrel tutor team runs a Kanban board. After 12 weeks the product lead asks the question every
stakeholder asks: "When will the remaining 40 items be done, and what can we promise for the next
four weeks?" Story-point estimates have been wrong every sprint. You answer from history instead:
weekly throughput, cycle times, a Monte Carlo forecast with confidence levels, and Little's law as a
sanity check.

## What you have

| Path | What it is |
|---|---|
| `data/done_items.csv` | 57 finished items: started, done, type (week 6 had zero: the team was at a conference) |
| `kanban/forecast.py` | functions to implement (TODO) and `make run` |

## Requirements

Docstrings carry the exact rules: weekly throughput Mon-Sun with zero weeks kept; cycle time in days;
nearest-rank percentiles; a seeded Monte Carlo that samples weekly throughput with replacement until
the backlog is done (with a cap and an error on all-zero history); a finish date at a given confidence;
"how many items in N weeks" at a confidence (the low end of the distribution); Little's law.

## Acceptance criteria (what the grader checks)

- Throughput, week boundaries, cycle-time percentiles on the data and on hand cases.
- Exact seeded simulation results, the cap and the error case.
- Finish dates at 50/85/95% and items in 4 weeks at 85%.
- `ANSWER.md`: the message you would send the product lead (a range, not a date), why the zero week
  stays in the sample, and what would make the forecast wrong (scope growth, changing WIP, item splitting).

## How to run

```bash
make setup
make test
make run
# fill in ANSWER.md, then from workbooks/: /grade javaai/x-2
make clean
```
