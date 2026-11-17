# Reference: platform/w1-t1 Prod apply denied after the WIF hardening PR

## Root cause

PR #388 replaced the `tf-apply` federation binding

    principalSet://.../workloadIdentityPools/github/attribute.repository/tessellate/platform-foundation

with the exact subject

    principal://.../workloadIdentityPools/github/subject/repo:tessellate/platform-foundation:ref:refs/heads/main

The intent was right (only main may apply), but the subject format was wrong for this job. GitHub builds
the OIDC `sub` claim from the job context: a job that references an environment gets
`repo:<owner>/<repo>:environment:<name>`; only jobs without an environment get `...:ref:<ref>`; pull
requests get `...:pull_request`. The apply job declares `environment: production`, so its token
(`evidence/claims/apply-run-4412.json`) has `sub = repo:tessellate/platform-foundation:environment:production`.
The provider maps `google.subject = assertion.sub`, so the federated principal is
`principal://.../subject/repo:tessellate/platform-foundation:environment:production`, which matches no
binding on tf-apply.

Evidence chain:
- audit log 09:12:03 `ExchangeToken` succeeds with that principalSubject (the provider condition is fine);
- audit log 09:12:08 `GenerateAccessToken` on tf-apply fails with PERMISSION_DENIED, same principal;
- audit log 08:41:55 `SetIAMPolicy` on tf-apply, made by tf-apply itself (the merge apply of #388, run
  4398, still authenticated through the old binding and installed the new one), shows the ref:main member;
- the diff in `pr-388.diff`; `make repro` reproduces DENIED at the iam step.

Red herrings: "or it may not exist" is the standard text of any generateAccessToken denial; the deleted
service account in the logs is `tf-apply-old` in `tsl-sandbox-legacy`. Granting
`roles/iam.serviceAccountTokenCreator` to `principalSet://.../*` is the wrong role for federation
(`roles/iam.workloadIdentityUser` is what lets a federated principal impersonate) and would let every
token the pool accepts, including pull requests, impersonate the apply SA: it undoes PR #388.

## Fix

`.grading/solution/infra/wif.tf.json`: the apply binding member becomes

    principal://iam.googleapis.com/projects/${local.ci_project_number}/locations/global/workloadIdentityPools/${local.pool_id}/subject/repo:${local.repo}:environment:production

This keeps the intent: only jobs in the `production` environment of this repository can impersonate
tf-apply, and the environment's protection rules (required reviewers, deployment branch main) are what
make that equivalent to "main only, reviewed". Removing `environment: production` from the job would also
make the old subject match, but it drops the reviewer gate, so the grader rejects it.

Alternatives worth mentioning: map `attribute.environment = assertion.environment` and bind a
principalSet on a composite attribute such as `assertion.repository + ':' + assertion.environment`;
or pin `job_workflow_ref` when the apply moves to a reusable workflow. Prevention: a CI test that runs the
bindings against sample claims for each job before merge, and an alert on GenerateAccessToken denials
for tf-apply.
