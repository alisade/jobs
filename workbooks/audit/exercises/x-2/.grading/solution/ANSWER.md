# ANSWER: audit/x-2 ControlPilot production architecture

## Approach

Started from the committee's conditions and mapped each to a mechanism, then let the strictest
ones (immutable 7-year retention, no keys, ControlPilot under CM-03) drive the platform choices.

## Fix

1. State, review gate and logs live in Azure (Durable Functions, Azure SQL, WORM Blob); Google hosts only the model.
2. Workload Identity Federation from a managed identity, no service account keys, org policy blocks keys.
3. The evidence-reading agent has no write tools; writes need an approval token from the review gate.
4. Idempotency keys on every side effect so retries and resumes never duplicate GRC issues or workpapers.
5. Prompts, model version and tool permissions are released through CM-03 with an eval gate on exception recall.

## Trade-offs / what I would do in production

Rejected hosting the agent on Agent Runtime: simpler, but state and retention would sit outside
MFH's immutable logging. Rejected a home-grown loop in favour of ADK for tools and sessions, kept
behind our own gateway. Durable Functions over a queue-and-table design for replay and external
events. Accepted residual risk: a manipulated extraction can reach a reviewer, mitigated by
mandatory citations and the reviewer gate.
