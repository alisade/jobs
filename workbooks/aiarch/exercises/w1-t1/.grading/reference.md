# Reference: aiarch/w1-t1

Root cause: `trust/gitlab-deploy-prod.json` still requires
`gitlab.com:sub == project_path:harborpoint/lighthouse/platform:ref_type:branch:ref:main` (from
when prod deployed from main). Tag pipelines send `ref_type:tag:ref:v2.4.0`. Fix: `StringLike` on
`project_path:harborpoint/lighthouse/platform:ref_type:tag:ref:v*`, audience still pinned. The
thumbprint is irrelevant for gitlab.com and would break dev too. "Protected tags only" cannot be
expressed in IAM (only aud and sub are condition keys for this provider); it is enforced by
GitLab protected tags and the protected production environment with approvals.
