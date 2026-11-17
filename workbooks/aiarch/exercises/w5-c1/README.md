# aiarch/w5-c1 - One DynamoDB table for Lighthouse platform state

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 5 (Thu: DynamoDB for agent state; Fri: cost per conversation)

## Scenario

AgentCore Memory holds the conversations; Strands session storage holds agent state. What is
left belongs to the platform, and Harbor Point Mutual wants it in one on-demand DynamoDB table
(`lighthouse-state`): a session index per user, idempotency records so a retried tool call
does not file a second access request, a cost ledger per agent per day fed by the `gen_ai.*`
attributes of the model-call spans, and approval state with optimistic locking.

Tests run against moto (`mock_aws`): no AWS account. `data/spans.jsonl` holds exported
model-call spans; `data/prices.json` holds USD per million tokens (fictional).

## Access patterns

1. Sessions for one user in the last N days, newest first.
2. One session by id.
3. Has this tool side effect already run (and what did it return)?
4. Cost for one agent by day over a date range.
5. Cost for all agents on one day.
6. Approve or reject a request exactly once, safely under concurrency.

## Requirements (`lighthouse_state/store.py`)

1. `create_table`: keys and at most two GSIs that serve all six patterns, on-demand, TTL on
   attribute `ttl` (epoch seconds).
2. `start_session`: item with a 30-day TTL in epoch seconds; a duplicate (same user, start and
   id) fails. `recent_sessions` is a Query (no Scan), window `now - days` to `now`, newest
   first. `get_session` by id.
3. `run_once(key, fn, now)`: a conditional write (`attribute_not_exists`) claims the key before
   `fn` runs; a retry after success returns the stored result without calling `fn`; a call
   while the first is still running raises `InProgress`; if `fn` raises, the claim is removed
   so a retry can run; idempotency records expire through TTL.
4. `record_usage(span, prices)`: input, output and cache-read tokens times the model's prices,
   stored as integer micro-dollars and added atomically (`ADD`) to the agent's day; also
   counts calls. Unknown model raises `KeyError`. `daily_cost` and `cost_for_day` return USD.
5. `create_approval` and `decide(request_id, decision, approver, expected_version)`: a
   conditional update on version and state; stale version or a second decision raises
   `Conflict`; returns the new version.

## Acceptance criteria (what the grader checks)

- TTL and index limits, query windows, duplicate protection, idempotency including failure and
  in-progress, exact cost sums with cache tokens, all-agents-per-day, optimistic locking.
- `ANSWER.md`: your key design as a table (pattern, key, index), what goes in AgentCore Memory
  vs this table and why, and how you would stop one busy tenant from creating a hot partition.

## How to run

```bash
make setup     # builds aiarch/.venv once (boto3, moto)
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/w5-c1
make clean
```

## What to submit

`lighthouse_state/store.py` and `ANSWER.md`.
