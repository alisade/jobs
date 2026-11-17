# Rubric: aiarch/w1-t1 Release tag cannot deploy to prod
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 35 | Full: the prod trust policy pins sub to ref_type:branch:ref:main with StringEquals, the tag token carries ref_type:tag:ref:v2.4.0, and dev works because its token matches. Partial: "trust policy wrong" without the claim. Zero: thumbprint or identity policy. |
| 3 | Evidence | 15 | Quotes the sub from the claims file or CloudTrail userIdentity, make check output, CHG-8812 vs CHG-7730. |
| 4 | Fix quality | 10 | StringLike on sub scoped to this project and ref_type:tag:ref:v*, aud still pinned; no project-wide wildcard; dev untouched. |
| 5 | Production view | 10 | Explains that IAM sees only aud and sub, so protected tags and the protected environment in GitLab do the rest; thumbprint not used for gitlab.com; trust changes reviewed with process changes. |
Total: 100
