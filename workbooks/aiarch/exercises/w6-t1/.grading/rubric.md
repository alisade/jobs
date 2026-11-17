# Rubric: aiarch/w6-t1 Prod deploy blocked by an SCP
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause | 35 | Full: the CDK CloudFormation exec role makes IAM calls, the SCP exempts only gitlab-deploy-*, dev predates the SCP. Zero: permissions boundary or identity policy. |
| 3 | Evidence | 15 | sessionIssuer and invokedBy in CloudTrail, the stack event text, the assume chain, the attach date. |
| 4 | Fix quality | 10 | Exempts the exec role pattern and break-glass only; no cdk-* or role/* wildcard; GitLab and deploy roles not exempt. |
| 5 | Production view | 10 | Explicit vs implicit deny wording, naming as a boundary and its limits, bootstrap qualifier, testing SCPs before attach. |
Total: 100
