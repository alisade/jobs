# backend/w6-t1 - Lead workflows stuck after Tuesday's deploy

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 6 (Mon: durable execution and determinism; Wed: workflow versioning and replay tests)

## Scenario

`keystone-workflows` runs Lumenfold's lead assignment on Temporal: score the lead, propose an owner,
wait up to 48 hours for the regional manager, escalate to sales ops, then assign. Release 2026.45
(PR #812) added an enrichment step and an "approve by" deadline for the manager inbox. Within twenty
minutes the workflow task failure alert fired. Sales ops says approvals on leads from before the
deploy do nothing, and the deadline in the inbox moves every time the page refreshes. New leads seem
fine. On call blames the enrichment vendor's timeouts and is preparing a timeout hotfix. A rollback
would break the leads that already started on 2026.45.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGER.md` | the page and the incident channel timeline |
| `evidence/worker-2026-11-10.log` | worker log excerpt after the rollout |
| `evidence/pr-812.diff` | the change that shipped, with review comments |
| `histories/*.json` | four histories exported from executions that started on 2026.44 |
| `keystone_workflows/` | current code (2026.45): `lead_workflow.py`, activities, models, `replay.py`, test rig |
| `tests/` | visible tests: a new execution end to end, and a replay of every history |

Everything runs offline: the Temporal Python SDK `Replayer` needs no server, and the tests use the
time-skipping test server that `make setup` downloads once into `backend/.temporal`.

## Your task

1. Find the root cause. `make replay` shows what a worker sees when it picks up an old execution.
   Back the cause with evidence from the log, the diff and the histories.
2. Fix `keystone_workflows/lead_workflow.py` so that every recorded history replays cleanly and
   executions that start on the new code still run `enrich_lead`. Do not delete the histories or
   change the activity names.
3. Make the SLA deadline deterministic and turn the workflow sandbox back on.
4. Fill in `ANSWER.md`: root cause with evidence, why the timeout theory is wrong, the fix, how you
   verified it, and how you would roll it out and later remove the compatibility code.

## Acceptance criteria (what the grader checks)

- Every history in `histories/` replays without error.
- A new execution records a version marker in its history and calls `enrich_lead` once.
- `sla_deadline` does not change between replays and equals workflow time at proposal + 48 hours.
- The workflow is sandboxed.
- `ANSWER.md`: root cause and evidence carry most of the points.

## How to run

```bash
make setup      # venv + Temporal test server (one time)
make replay     # replay histories/*.json against your code
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade backend/w6-t1
make clean
```
