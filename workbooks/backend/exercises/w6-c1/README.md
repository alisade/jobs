# backend/w6-c1 - Lead assignment workflow with manager approval

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 6 (Mon: durable execution; Tue: signals, queries, updates and timers; Thu: workflow primitives)

## Scenario

In the old CRM, lead assignment was a tangle of assignment rules, an approval process and a
scheduled flow that "usually" escalated stale approvals. Keystone replaces it with a workflow
primitive in `keystone-workflows` that product teams and agents start through an API: an agent
can propose an owner for a lead, but only the lead's region manager can approve it, and nothing
may be assigned twice. Sales ops (Dana Whitfield) has two hard rules from the last CRM incident:
no lead waits more than 48 hours without someone in sales ops hearing about it, and after 72
hours it goes to the region's shared queue so it is not lost.

The spike in `keystone_workflows/workflow.py` handles the happy path once. Last month's accounts
API outage showed the other problem: the API committed an assignment and then returned a 504, the
caller retried, and the lead got two owners.

## What you have

| Path | What it is |
|---|---|
| `keystone_workflows/workflow.py` | **your code**: the `LeadAssignment` workflow |
| `keystone_workflows/activities.py` | activities (provided): `score_lead`, `propose_owner`, `escalate`, `assign_owner`, plus the fake accounts API (honours idempotency keys; can commit then fail) and a notifier |
| `keystone_workflows/models.py` | dataclasses for inputs, outputs and status; region managers and queues |
| `keystone_workflows/testkit.py` | test rig on the Temporal time-skipping test server (real SDK, offline) |
| `tests/` | visible happy-path test |

## Requirements

1. `run(lead)`: `score_lead`, then `propose_owner`, then state `awaiting_approval`.
2. Decisions: an `approve` **update** (`ApproveInput`, optional `owner_id` override) and a `reject`
   **signal** (`RejectInput`). The update's **validator** rejects anyone who is not
   `REGION_MANAGERS[lead.region]`, and any decision when one is already recorded or the workflow is not
   waiting; a rejected update must not change state (and is not written to history).
3. Timers: no decision within 48 h -> `escalate` to `SALES_OPS` (state `escalated`, `status.escalated`
   true); an approval or rejection still counts while escalated; no decision 24 h after that -> assign
   to `REGION_QUEUES[region]` and finish with outcome `queued`.
4. Approval -> `assign_owner` with an idempotency key derived from the workflow id (stable across
   activity retries and worker restarts), outcome `assigned`. Rejection -> outcome `rejected`, no
   assignment.
5. Activity options: timeouts on every activity, a retry policy, and `ValidationError` non-retryable
   (bad input must fail fast, not retry for an hour).
6. `status` query returns the `Status` dataclass at every stage.
7. Determinism: no wall clock, random or I/O in workflow code. A new worker must be able to replay
   the history and continue.

## Acceptance criteria (what the grader checks)

- Visible and hidden tests pass on the time-skipping server: approve, reject, validator rejection
  then a valid approval with an owner override, 48 h escalation then 72 h queue assignment (checked
  against workflow history time), approval while escalated, worker replaced mid-wait (full replay),
  exactly one assignment when the API commits and then fails, a `ValidationError` attempted once,
  duplicate decisions ignored.
- `ANSWER.md`: why update vs signal for approval, where the idempotency key comes from, and how
  you would version this workflow once executions are in flight.

## How to run

```bash
make setup      # shared venv + Temporal test server (first run downloads ~65 MB once)
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/w6-c1
make clean
```

Optional: `python -m keystone_workflows.worker` runs a worker against a local `temporal server
start-dev` if you have the Temporal CLI. The tests never need it.
