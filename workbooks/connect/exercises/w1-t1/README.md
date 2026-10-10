# connect/w1-t1 - "All specialists are busy" on repeat

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 1 (Tue: flow language, flow logs; Wed: routing and check staffing)

## Symptom

LFG's help desk shipped flow release 2026.10.07 at 07:00 ET. From about 14:00 ET, callers
report that the IVR keeps saying "All specialists for this request are busy. Connecting you
to the general help desk." and never connects; most hang up after a minute or two. It is
not only password resets. CloudWatch shows no flow errors. The IAM team thinks Okta rate
limiting on the reset API is to blame. Start with `incident/PAGE.txt`.

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the page and the cutover channel thread |
| `incident/release-notes-2026.10.07.md` | what shipped (CHG-48211) |
| `incident/exported-flows/` | the flow as exported before (2026.09.30) and after (2026.10.07) the release |
| `incident/flow-logs/` | CloudWatch flow logs for the afternoon (one JSON object per block executed) |
| `incident/contact-records-2026-10-07.jsonl` | contact records (subset of fields) |
| `incident/realtime-queue-metrics-2026-10-07.csv` | 15-minute real-time queue snapshots |
| `incident/lambda-lfg-password-reset-2026-10-07.log`, `incident/cloudwatch-metrics-2026-10-07.txt` | Lambda logs and metrics |
| `flows/helpdesk-inbound.json` | your working copy (identical to what is deployed) |
| `scripts/simulate.js` | replays a caller through your working copy with the local interpreter |

`make setup` regenerates `incident/` deterministically from the deployed flow.

## Your task

1. Find the root cause. Prove it from the bundle (flow logs, contact records, metrics) and
   from the flow JSON, not from the release notes alone: what loops, between which blocks,
   why it started at 14:00 and not at 07:00, and why no metric alarmed.
2. Rule the Okta theory in or out with evidence.
3. Fix `flows/helpdesk-inbound.json` without losing what CHG-48211 was for (never transfer a
   caller to a queue with nobody staffed).
4. Verify with `make lint`, `make simulate`, `make test`.
5. Write `ANSWER.md`: Approach, Root cause (commands + output excerpts), Fix and
   verification, Trade-offs / prevention (how the pipeline should have caught this).

## Acceptance criteria (what the grader checks)

- Lint clean; no staffing check pinned to the wrong queue; no cycle without a bound.
- With PasswordReset unstaffed: option 2, VIP and outage callers reach their own queues
  with no busy message; failed resets overflow once to GeneralSupport.
- With nobody staffed anywhere: a message and a clean disconnect, never a loop, and nobody
  is transferred into an empty GeneralSupport queue.
- Every option x VIP x staffing combination terminates.
- `ANSWER.md` names the mechanism precisely with evidence; a fixed flow with a hand-waved
  explanation does not pass.

## How to run

```bash
make setup                                   # toolchain + incident bundle
make simulate INPUTS=2 PR_STAFFED=0          # replay against your working copy (VIP=true, RESET=SENT, GS_STAFFED=0 ...)
make lint
make test
# from workbooks/: /grade connect/w1-t1
make clean
```

Useful: `grep '"check-staffing"' incident/flow-logs/*.log | head`,
`jq -r 'select(.Identifier=="check-staffing") | [.Timestamp,.Results,.Parameters.QueueId] | @tsv' incident/flow-logs/*.log | sort | uniq -c | head`,
`diff incident/exported-flows/helpdesk-inbound.2026.09.30.json incident/exported-flows/helpdesk-inbound.2026.10.07.json`.
