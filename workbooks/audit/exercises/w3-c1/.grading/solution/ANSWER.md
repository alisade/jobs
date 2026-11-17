# ANSWER: audit/w3-c1 ADK CM-03 tester

## Approach

Guardrails are ADK callbacks because they must hold even when the model misbehaves: a callback is
deterministic code that runs around every tool call, while an instruction is a request. The agent
only gets the read tools and record_result; the before-tool callback also allow-lists, scopes ids to
the sample and enforces a budget kept in session state.

## Fix

guard.py: before/after callbacks and a canonical-JSON digest. agent.py: allowed tools only, Runner
with an in-memory session holding sample_ids, final text captured, strict summary models, and a
cross-check against the results recorded in state. I tested out-of-sample ids, unlinked PRs, the
write tool, the budget and summaries that disagree with state.

## Trade-offs / what I would do in production

The log lets an auditor replay the run: which records were read, in what order, what was blocked
and why, and a digest that ties each result to the stored record. In production it goes to
append-only storage (immutable blob), with the model version and prompt hash. On Gemini Enterprise
Agent Platform the same callbacks deploy with the agent; sessions move to the managed session
service.
