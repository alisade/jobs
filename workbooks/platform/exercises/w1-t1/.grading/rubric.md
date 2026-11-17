# Rubric: platform/w1-t1 Prod apply denied after the WIF hardening PR
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: PR #388 rebound tf-apply's `roles/iam.workloadIdentityUser` to `principal://.../subject/repo:tessellate/platform-foundation:ref:refs/heads/main`, but a job that runs in a GitHub environment gets an OIDC `sub` of `repo:<org>/<repo>:environment:<name>`, so the apply job (environment production) never matches; STS exchange succeeds, impersonation (generateAccessToken) is denied. Also explains why it surfaced on run 4412 and not on the merge of #388 (that apply ran with the old binding and applied the new one). Partial (10-15): "the binding is wrong" without the sub format or which step fails. Zero: blames the provider condition, a deleted service account or a missing Token Creator role. |
| 3 | Evidence | 20 | Full: at least three of: the apply claims `sub` and `environment`, the audit log ExchangeToken success vs GenerateAccessToken PERMISSION_DENIED with the principalSubject, the SetIAMPolicy entry showing the new member, the diff line, the simulator output. Partial: one or two. Zero: assertion only. |
| 4 | Red herrings handled | 10 | Rules out "tf-apply was deleted" (the deleted SA is tf-apply-old in tsl-sandbox-legacy; "or it may not exist" is the generic text for any denial) and rejects the pool-wide Token Creator grant (wrong role for federation and would let every token in the pool, including PRs, impersonate the apply SA). |
| 5 | Fix quality | 10 | Binds the exact environment subject (or an equivalent narrow principal), keeps the owner condition, keeps tf-plan for PRs, keeps `environment: production` (removing it would make the old subject match but drop the required-reviewer gate). Mentions removing the now-unused `attribute.ref` or using it deliberately. |
| 6 | Prevention | 5 | Concrete: a CI check that simulates the bindings against sample token claims for each job (like this simulator), environment protection rules (required reviewers, main only), break-glass path documented, alert on GenerateAccessToken denials for tf-apply. |
Total: 100
