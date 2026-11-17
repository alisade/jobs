# ANSWER: backend/w6-t1 Lead workflows stuck after Tuesday's deploy

## Approach

Ran `make replay` against the four exported histories: all four failed. Compared the failure text
with the worker log, then read PR #812 and the event order in `histories/lead-7f3a21-awaiting.json`.

## Root cause

Workflow nondeterminism introduced by PR #812. Executions that started on 2026.44 have
`score_lead -> propose_owner` recorded in their event history. When a 2026.45 worker picks one up (an
approve signal arrives), it replays the history with the new code, which now issues `score_lead ->
enrich_lead -> propose_owner`. The second command no longer matches the second recorded event, so the
SDK fails the workflow task and retries it forever. The approval never progresses.

```
worker log 14:18:22  NondeterminismError: [TMPRL1100] Nondeterminism error: Activity type of scheduled
                     event 'propose_owner' does not match activity type of activity command 'enrich_lead'
make replay (before) FAIL histories/lead-7f3a21-awaiting.json ... (same error for all four)
pr-812.diff          + firmo = await workflow.execute_activity_method(LeadActivities.enrich_lead, ...)
```

Only pre-deploy executions are affected (Priya: "new leads created since 14:05 look fine"), which is
the signature of a replay problem, not a runtime one.

Second defect in the same PR: `sla_deadline = datetime.now(timezone.utc) + 48h`. Workflow code must
take time from the history (`workflow.now()`); wall-clock time gives a different value on every replay,
which is exactly what sales ops saw (log 14:27 `sla_deadline=2026-11-12T14:07:03` then 14:31
`sla_deadline=2026-11-12T14:31:11` for the same lead). The author disabled the sandbox
(`sandboxed=False`) because it raised `RestrictedWorkflowAccessError` on `datetime.now`: the sandbox
was reporting this bug and was switched off instead.

Red herring: the `enrich_lead` timeouts are ordinary activity retries on new executions (attempt 1 times
out, attempt 2 completes in under a second). Activity failures are retried by the server and never cause
a workflow task failure; raising the timeout would change nothing for the stuck leads.

## Fix

- Wrapped the new activity in `if workflow.patched("enrich-lead-before-propose"):`. On replay of an old
  history without the marker, `patched` returns False and the code follows the old command sequence;
  new executions record the marker and run `enrich_lead`.
- `sla_deadline = workflow.now() + APPROVAL_WINDOW`.
- Removed `sandboxed=False`.
- Verified: `make replay` prints OK for all four histories; `make test` passes (new execution enriches
  and assigns; histories replay). The stuck tasks recover on their next retry once the fixed worker is
  deployed, with no manual intervention.

## Trade-offs / what I would do in production

Deploy 2026.45.1 as a normal rollout; the failing tasks retry and succeed. Keep the patch until every
execution that started before the marker existed has closed (at most 48 h + escalation window, check
with a visibility query), then replace it with `workflow.deprecate_patch(...)`, and remove it in a third
deploy. Add a CI job that replays a sample of recent production histories against every workflow
change, and keep the sandbox on; both would have caught this before Tuesday. Worker versioning (build
ids) is the alternative when changes are large.
