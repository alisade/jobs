# Reference: backend/w6-c1 Lead assignment workflow with manager approval

Solution: `.grading/solution/keystone_workflows/workflow.py`.

- Waits: `await workflow.wait_condition(decided, timeout=48h)` raises `asyncio.TimeoutError` on
  expiry. That is a durable timer in history, not a wall-clock sleep, so it survives restarts and
  the time-skipping server can jump over it.
- Escalation: activity `escalate`, set `status.escalated`, wait 24 h more, then assign to the region
  queue. Decisions during the escalation window still count.
- Approve as an **update** with a **validator**: the caller (the manager's UI or an API) gets a
  synchronous result or an error, and a rejected update is never written to history, so a wrong
  approver cannot even appear in the audit trail of the workflow. Reject as a signal is fine because
  it needs no answer; it is ignored once a decision exists.
- Assignment key: `f"{workflow.info().workflow_id}:assign"`. Activity retries reuse the same input,
  worker restarts replay the same value, and the accounts API dedupes on it. A uuid4 generated in
  workflow code is also non-deterministic.
- Activity options: start_to_close timeouts, RetryPolicy with backoff, `non_retryable_error_types=["ValidationError"]`.

Interview angles:
- Why Temporal over a queue + cron for this? 72 h human waits, timers, exactly one owner, and the
  history as an audit trail; a cron sweeper re-implements all of it with worse failure modes.
- Step Functions comparison: callback tokens (`.waitForTaskToken`) instead of updates, JSON states
  instead of code, no validator before history, 1-year max duration, easier IAM integration.
- Changing this workflow with executions in flight: `workflow.patched("...")` branches, or worker
  versioning (build ids) so old executions stay on old code.
- Agents: an agent tool `propose_lead_assignment` starts this workflow and returns the workflow id;
  approval stays with a human, enforced by the validator, not by the agent's prompt.
