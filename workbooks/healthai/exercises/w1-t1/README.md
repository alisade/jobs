# healthai/w1-t1 - The CMS clock report says zero late decisions

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 1 (Thu CMS-0057-F clocks; Mon datetime and asyncio basics)

## Scenario

Kestrel Health Plan (fictional) has to publish prior authorization metrics for its CMS-0057-F impacted
lines (Medicare Advantage, Medicaid managed care, CHIP managed care). The Q4 draft shows **zero late
standard decisions**. The external auditor disagrees. Compliance opened `incident/ticket.md`. The same
deadline code feeds the nurse reviewers' "time remaining" column, so this is not only a reporting bug.

## What you have

| Path | What it is |
|---|---|
| `incident/ticket.md` | the ticket, as Compliance wrote it |
| `incident/report_run.log`, `incident/audit_sample.csv` | produced by `make setup`: last report run, auditor sample |
| `data/cases.csv` | synthetic Q4 case export (640 cases, generated with a fixed seed by `make setup`) |
| `clockreport/deadlines.py`, `clockreport/report.py` | the deadline helper and the metrics report |
| `findings.json` | your machine-checked findings |

## Your task

1. Reproduce: `make setup`, read the log and `out/pa_metrics.json`, compare with the audit sample.
2. Find the root cause. Decide whether the DST warnings in the log matter, with evidence.
3. Fix it in the code, re-run `make report`, and fill in `findings.json`:
   `root_cause_file`, `root_cause_function`, `late_standard_decisions`, `late_expedited_decisions`
   (from the fixed report) and `audit_sample_confirmed` (the audit sample ids your fixed report also
   flags late).
4. Write `ANSWER.md`: root cause with evidence (at least two case ids with received time, the wrong and
   the right deadline, and the decision time), how you verified the fix, the DST question, and how you
   would stop this class of bug reaching a regulatory report again.

## Acceptance criteria (what the grader checks)

- Standard deadlines are 7 calendar days on the plan's wall clock, from any weekday including weekends;
  expedited stays 72 hours.
- The report's late counts and late case ids match an independent computation on a freshly generated
  export; every audit-sample case is reported late.
- `findings.json` is filled in and consistent.

## Run

```
make setup     # data, incident bundle, first (wrong) report
make report    # re-run after your fix
make test      # visible tests
# fill in ANSWER.md and findings.json, then: /grade healthai/w1-t1
make clean
```
