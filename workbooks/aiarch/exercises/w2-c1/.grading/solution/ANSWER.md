# ANSWER: aiarch/w2-c1

## Approach

Agents as tools: the orchestrator only sees two tools, each of which builds a specialist Agent
with its own model, prompt, tools and hooks and returns its final text. Hooks are registered on
every agent, so the audit and the delete block cannot be bypassed by a specialist.

## Fix

- tools.py: format, enum and length checks raising ToolInputError with the allowed values;
  trimmed outputs; requester from the session closure.
- hooks.py: AuditHook cancels delete_* in BeforeToolCallEvent and records status in
  AfterToolCallEvent; BudgetHook counts BeforeModelCallEvent and raises past the cap.
- agents.py: build_orchestrator as described. Verified with make test.

## Trade-offs / what I would do in production

- A prompt rule is advice; a hook is enforcement. Anything that must hold goes in a hook, Cedar
  policy or IAM, not the system prompt.
- Agents as tools is the easiest pattern to trace and bound. A swarm fits open-ended handoffs,
  a graph fits branching approval flows, a workflow fits fixed parallel tasks.
- Use a small model for the orchestrator and pay for a larger one only in specialists that need
  it; send the audit records to CloudWatch as structured logs or OTEL span events.
