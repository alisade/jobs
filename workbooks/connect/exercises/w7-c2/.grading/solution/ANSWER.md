# ANSWER: connect/w7-c2 Agent workspace app

## Approach

Turned each pilot complaint into a failing test against the fake ContactEventSource (stale context,
bad slots, entitlement leak, duplicates, silent failure, "*" attribute request), then fixed the pure
functions (rank, guide, api) before the component.

## Fix

Ref-tracked current contact with stale-result guards and stable handlers unsubscribed on unmount;
HANDOFF_KEYS-only attribute request; tolerant slot parsing; guide fallback, verified pre-check and
required-step gating; resolve with completed-step work notes and visible, retryable failures;
ranking with default-deny entitlement, 0.4 floor, best-score dedupe, stable order, cap 5; backend
PATCH with bearer token and sys_id validation.

## Trade-offs / what I would do in production

Register as a third-party app with only the contact permissions it needs; backend auth via the
agent's SSO identity; entitlements from IdP groups applied in the retrieval filter, not just the UI;
log suggestion clicks to tune ranking; keep simple checklists as step-by-step guides instead of code.
