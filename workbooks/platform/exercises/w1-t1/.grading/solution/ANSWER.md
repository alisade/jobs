# ANSWER: platform/w1-t1 Prod apply denied after the WIF hardening PR

## Approach

Started from the run log (403 on generateAccessToken, so the failure is the impersonation step, not the
STS exchange), then the audit logs to confirm, then the claims and the PR diff.

## Root cause

PR #388 bound tf-apply's roles/iam.workloadIdentityUser to
`principal://.../subject/repo:tessellate/platform-foundation:ref:refs/heads/main`. The apply job runs in
`environment: production`, and GitHub sets `sub` to `repo:tessellate/platform-foundation:environment:production`
for jobs that use an environment (claims file: `"sub": "repo:tessellate/platform-foundation:environment:production"`).
Audit log: ExchangeToken at 09:12:03 succeeded for that principal; GenerateAccessToken at 09:12:08 was
PERMISSION_DENIED for the same principal. The 08:41:55 SetIAMPolicy entry shows the ref:main member, set
by the merge apply of #388 itself, which still used the old repository-wide binding. `make repro` shows
DENIED at iam.

Red herrings: the deleted SA is tf-apply-old in tsl-sandbox-legacy, and "or it may not exist" is the
generic denial text. A pool-wide Token Creator grant is the wrong role and would let PR tokens apply.

## Fix

Bound tf-apply to `principal://.../subject/repo:tessellate/platform-foundation:environment:production`.
Verified with the simulator: run 4412 gets tf-apply; PR, feature-branch, main without environment,
staging, other repo and fork tokens are denied; PR plans still get tf-plan.

## Trade-offs / what I would do in production

Relies on the production environment's protection rules (required reviewers, main only). Add a CI test
that runs the bindings against sample claims per job before merge, and alert on denied
GenerateAccessToken for tf-apply. Same idea as the `sub` condition in an AWS IAM OIDC trust policy, which
has the same environment-vs-ref trap.
