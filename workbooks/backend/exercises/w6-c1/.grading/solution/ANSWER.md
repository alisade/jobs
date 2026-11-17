# ANSWER: backend/w6-c1 Lead assignment workflow with manager approval

## Approach

The workflow keeps its state in fields (`_approval`, `_rejection`, `_status`) and does every side
effect in an activity. The decision wait is `wait_condition` with a 48 h timeout; on timeout it
escalates and waits 24 h more, then assigns to the region queue. These are durable timers, so a
worker restart or a rollout does not lose them.

Approve is an update with a validator because the manager's client needs a yes/no answer and a
wrong approver must be refused before anything is recorded: rejected updates never reach history.
Reject is a signal because it needs no reply and is ignored once a decision exists.

## Fix

- 48 h / 24 h timers with escalation and queue fallback; reject signal; status query at every stage.
- Validator: region manager only, no decision when one exists or when the workflow is not waiting.
- Assign with key `<workflow id>:assign`; every activity has a timeout and a retry policy with
  `ValidationError` non-retryable.
Verified with `make test`, then by stopping the worker mid-wait in a scratch test and approving
through a fresh worker.

## Trade-offs / what I would do in production

- Versioning: once executions are in flight, any change in command order goes behind
  `workflow.patched(...)` or onto a new worker build id.
- Expose the primitive through a typed API (POST /v1/lead-assignments) and search attributes
  (region, approver) so managers can list what waits on them; product teams never touch the client.
- Agents may start the workflow (propose) but approval stays a human update guarded by the
  validator, so prompt injection cannot assign a lead.
