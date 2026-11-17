# ANSWER: aiarch/w1-t1 Release tag cannot deploy to prod

## Approach

Read the page, then compared the two decoded tokens and ran `make check` against both trust
policies. The CloudTrail event confirms the role and the web identity user.

## Root cause

The prod role trust policy still pins `gitlab.com:sub` with `StringEquals` to
`project_path:harborpoint/lighthouse/platform:ref_type:branch:ref:main`, from CHG-7730 when prod
deployed from main. CHG-8812 moved prod to tags, but nobody updated `trust/`. The v2.4.0 job's
token has `sub = project_path:harborpoint/lighthouse/platform:ref_type:tag:ref:v2.4.0`
(`incident/claims-tag-v2.4.0-deploy-prod.json`, and `userIdentity.userName` in the CloudTrail
event), so the condition fails and STS returns AccessDenied. The dev job's token is
`ref_type:branch:ref:main`, which matches the dev role, so dev works. `make check` printed
ALLOW for dev and DENY for prod.

The thumbprint is a red herring: for gitlab.com AWS validates the IdP with its own trusted CA
library, and a thumbprint problem would fail every job, including dev.

## Fix

`StringEquals gitlab.com:aud https://gitlab.com` stays. `gitlab.com:sub` is now `StringLike`
`project_path:harborpoint/lighthouse/platform:ref_type:tag:ref:v*`. Verified with `make check`
(both ALLOW) and `make test`. Branches, forks and other groups are denied because the project
path and ref type are pinned.

## Trade-offs / what I would do in production

- IAM can only see `aud` and `sub`, so "protected tags only" is enforced in GitLab: protected
  tags `v*` (only maintainers can create them) plus the protected `production` environment with
  an approval rule. The trust policy narrows to tags of this project; GitLab narrows who can
  make one.
- Keep one deploy role per account and environment, and change trust policies in the same MR as
  the release-process change so they cannot drift again.
- Add a pre-release smoke job that assumes the prod role read-only on a dry-run tag.
