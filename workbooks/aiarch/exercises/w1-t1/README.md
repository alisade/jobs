# aiarch/w1-t1 - Release tag v2.4.0 cannot deploy to prod

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** Week 1 (Fri: GitLab CI/CD with OIDC to AWS)

## Symptom

Harbor Point Mutual moved the Lighthouse platform to tag-based releases last week (CHG-8812):
`main` deploys to dev automatically, prod deploys only from protected release tags `vX.Y.Z`,
manually, through the `production` environment. The first release, `v2.4.0`, is stuck: the
`deploy-prod` job fails in `before_script` with `AccessDenied` from STS. `deploy-dev` on
`main` still works with the same OIDC template. On-call suspects the OIDC provider thumbprint.
Read `incident/PAGE.txt` first (created by `make setup`).

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the ticket and on-call notes |
| `incident/job-8842390-deploy-prod.log` | the failing job log |
| `incident/claims-*.json` | decoded `id_token` claims for the working dev job and the failing prod job |
| `incident/cloudtrail-assume-role-with-web-identity.json` | the CloudTrail event in the prod account |
| `incident/oidc-provider-prod.json` | the prod OIDC provider as exported |
| `trust/gitlab-deploy-{dev,prod}.json` | trust policies of the two deploy roles (edit these) |
| `.gitlab-ci.yml` | the pipeline |
| `oidccheck/` | evaluates a trust policy against decoded claims the way STS does (works as shipped) |

## Your task

1. Find the root cause from the evidence. Say which claim fails which condition, and why the
   dev job works.
2. Fix it with the smallest change that implements CHG-8812: release tags `v*` of
   `harborpoint/lighthouse/platform` may assume `gitlab-deploy-prod`; `main`, other branches,
   other tags, other projects and other audiences may not. Keep the dev role as it is.
3. Keep the pipeline's prod job tag-only, manual and on the `production` environment.
4. Write `ANSWER.md`: Approach, Root cause (with evidence), Fix and verification, Trade-offs.
   Say whether the thumbprint matters and what actually enforces "protected tags only",
   given that IAM can only see `aud` and `sub` from a GitLab token.

## Acceptance criteria (what the grader checks)

- Trust policy decisions for tag, branch, fork, other-group and wrong-audience tokens.
- The dev role and the pipeline guard rails are unchanged.
- `ANSWER.md` names the `sub` claim mismatch with evidence and handles the red herring.

## How to run

```bash
make setup     # evidence bundle + aiarch/.venv
make check     # evaluate both recorded tokens against the current trust policies
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/w1-t1
make clean
```

## What to submit

`trust/gitlab-deploy-prod.json` (and `.gitlab-ci.yml` if you changed it), and `ANSWER.md`.
