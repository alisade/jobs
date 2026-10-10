# connect/w4-t1 - Wave 2 parallel run fails migration validation

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 4 (migration validation testing; Avaya time-of-day and holiday vectoring vs Connect hours of operation and overrides)

## Symptom

Wave 2 of the LFG migration moves the main help desk (Avaya VDN 47100, vector 14) to Amazon
Connect. The number port is booked for Monday 2026-10-19 06:00 ET and the go/no-go gate is a
100% green migration-validation suite. Friday night's run is red. The Monterrey night shift says
parallel-run test calls after 16:00 hear "the help desk is closed", a 03:10 test call reached the
menu and queued, and the Connect admin suspects yesterday's routing-profile release. The Pune
factory reviewed the translated flow against the vector line by line and says it matches.
Start with `incident/PAGE.txt`.

## What you have

| Path | What it is |
|---|---|
| `incident/` (created by `make setup`) | PAGE and Slack thread, validation report, CloudWatch flow logs for two contacts, CTRs from the parallel-run DID, the 2026-10-08 release diff |
| `legacy/vector-14-hd-main.txt`, `legacy/holiday-table-3.txt` | the Avaya CM source of truth (CM clock: America/New_York) |
| `flows/helpdesk-inbound-migrated.json` | the translated Connect flow (wave 2) |
| `config/` | the migration repo's Connect configuration as exported: hours of operation, hours overrides, routing profiles, resource mapping |
| `tools/validate.js`, `tools/hours.js`, `tools/avaya.js` | the validation harness: legacy interpreter, hours evaluator, Connect simulator. Treat as the environment, not the suspect. |

## Your task

1. Find the root cause of the validation failures. Prove it with evidence from the bundle
   (report rows, flow logs, CTR timestamps, config), not just the config file.
2. Decide what the red herring is and rule it out with a reason.
3. Fix it in the migration repo files (the cause, not the symptom), keeping holiday handling
   intact and correct across daylight saving time changes.
4. Verify with `make validate DATES=...` across the parallel-run days and the November DST
   change, and `make test`.
5. Write `ANSWER.md`: Approach, Root cause (with commands and output excerpts), Fix (and how
   you verified it), Trade-offs / production follow-ups: why the factory's line-by-line review
   could not catch this, and what you would add to the pipeline so it never ships again.

## Acceptance criteria (what the grader checks)

- The validation suite is green for the parallel-run days, Columbus Day, Thanksgiving, and the
  days after both 2026 DST changes.
- Staffed hours stay 06:00-20:00 local, 7 days; all holiday overrides remain; the flow still
  checks holiday hours and help desk hours.
- `ANSWER.md` names the actual mechanism and backs it with evidence.

## How to run

```bash
make setup                                   # links the toolchain, writes incident/
make validate                                # the suite for 10/09, 10/12, 10/13
make validate DATES=2026-11-02,2026-03-09    # any NY dates
make bundle                                  # regenerate incident/ from the current config
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w4-t1
make clean
```
