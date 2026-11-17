# Rubric: aiarch/w3-c1 Lighthouse runtime and gateway stack in CDK
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 60 | points = 60 * passed / total from grade.sh |
| 2 | Least privilege and isolation | 15 | Bedrock on one profile and model only, SourceAccount on the trust, pull-only repo policy for named accounts, no NAT or IGW, endpoint SG 443 from the VPC only. |
| 3 | Release model | 10 | Immutable tag from a shared repo, endpoints pinned from config, fail-fast context; explains rollback by endpoint. |
| 4 | Code quality | 5 | Config-driven loops, small helpers, no copy-paste per env, L2 constructs used where they exist. |
| 5 | ANSWER.md | 10 | fromAsset vs fromEcrRepository argued, what the L2 adds to the role and why that is acceptable, a concrete pre-prod list. |
Total: 100
