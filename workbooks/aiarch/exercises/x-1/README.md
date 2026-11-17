# aiarch/x-1 - The on-demand session table throttles at 09:00

**Type:** troubleshooting (optional) | **Estimate:** 1-1.5 hours | **Study plan:** Week 7 add-on (DynamoDB drills; Week 5 Thu: DynamoDB modeling)

## Symptom

Every weekday between 09:00 and 09:20, when Harbor Point staff sign in, new Lighthouse sessions
fail to open: the app logs `ThrottlingException` from DynamoDB and users see "try again". The
`lighthouse-sessions` table is on-demand and its consumed write capacity is modest. On-call
wants to switch it to provisioned capacity with a high floor, or raise warm throughput.
Read `incident/PAGE.txt` first (created by `make setup`).

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the ticket and on-call notes |
| `incident/cloudwatch-metrics.csv` | per-minute table and index metrics around 09:00 |
| `incident/describe-table.json` | the table definition |
| `incident/app-logs.jsonl` | failing writes with the error text |
| `incident/status-counts.txt` | how many sessions are in each status |
| `lighthouse_sessions/sessions.py` | the session registry (edit this) |

## Your task

1. Find the root cause from the metrics, the table definition and the code. Explain why an
   on-demand table throttles here.
2. Fix `sessions.py`: the "all active sessions" query must keep working (the drain runbook and
   the dashboard use it), without one hot index partition; closed sessions must leave the
   index; TTL stays epoch seconds; the table stays on-demand.
3. Verify with `make test`.
4. Write `ANSWER.md`: Approach, Root cause (with evidence), Fix and verification, Trade-offs.
   Say whether provisioned capacity or warm throughput would have helped.

## Acceptance criteria (what the grader checks)

- Index key spread, stable shard per session, closed sessions gone from the index, paginated
  queries across shards, TTL and billing mode.
- `ANSWER.md` names the GSI hot partition and GSI back-pressure with evidence.

## How to run

```bash
make setup     # evidence bundle + aiarch/.venv
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/x-1
make clean
```

## What to submit

`lighthouse_sessions/sessions.py` and `ANSWER.md`.
