# ANSWER: aiarch/w4-t1

## Approach

Read the page, then the decision log for AR-1187 and AR-1102, the two tokens, and the policy set;
replayed with `make replay`.

## Root cause

policy2 (`forbid ... unless { principal.team == context.input.team }`) reads `principal.team`.
Partner IdP tokens carry no team claim (`claims-vk-ext-0042.json`), so the principal has no
`team` attribute and evaluating policy2 errors. In Cedar a policy whose evaluation errors is
skipped, it neither permits nor forbids. policy1 (managers approve) permits, nothing forbids,
so the decision is ALLOW. The log shows it: AR-1187 decision ALLOW, determining policy1, errors
"policy2: does not have the attribute team". The same pattern appears on 2026-11-07 in
LOG_ONLY (AR-1102): the review looked at decisions, not at the errors field. ENFORCE works;
rolling back would only stop blocking. Cedar has no "permits first": forbid wins, but only
when it evaluates.

## Fix

`unless { principal has team && principal.team == context.input.team }`: without a team the
condition is false, so the forbid applies and the approval is denied. Schema validation now
passes: the schema marks team optional, and the validator rejects access to an optional
attribute without a `has` guard, which would have caught this before LOG_ONLY.

## Trade-offs / what I would do in production

- Run `validate_policies` against the generated schema in CI and fail the merge on errors.
- Alarm on policy evaluation errors (Policy observability metrics) and review the errors field
  during LOG_ONLY, not just ALLOW/DENY.
- Fix the partner IdP mapping to release a team claim; until then contractors cannot approve.
- Keep an AVP or in-API check for "own team" as a second layer.
