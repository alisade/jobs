# ANSWER: modernize/w6-c1 Modernization pod kit

## Approach

Started from the failure log and the constraints: every incident had to map to a rule in the skill or
a gate in the playbook, and every increment had to fit a change window and keep a rollback.

## Fix

Key decisions: safety nets (characterization tests, enforcer, pr_guard, SBOM) are increments 1-2; JDK 21
ships on EAP 7.4 before Jakarta; corvane-commons is dual-published before consumers move; Jakarta moves one
module per PR; OIDC runs in shadow mode before enforcement; the skill measures first, verifies every step,
stops at majors, golden failures, security and shared APIs, and its never list mirrors the failure log;
reviewers use a rubric built on agent failure modes; the failure log closes only with a skill change plus an
eval case.

## Trade-offs / what I would do in production

Prove the skill first on claimdesk-rating, the module with the strictest partner contract. Measure:
agent PRs rejected at review and why, STOPs hit per week, escaped defects per increment, and eval pass rate
on each skill version. The cost is speed: per-module PRs and shadow mode add weeks, which the close freezes
force anyway.
