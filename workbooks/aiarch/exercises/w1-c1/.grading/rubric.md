# Rubric: aiarch/w1-c1 Lighthouse org guardrails (SCPs + RCP)
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh. About half the request cases are allow-guards that pass on the empty starter, so a score below 40 here means most deny rules are missing. |
| 2 | Condition logic | 15 | Full: negated operators used deliberately (StringNotEquals on aws:RequestedRegion, StringNotLike on bedrock:InferenceProfileArn so a missing key denies), ArnNotLike on aws:PrincipalArn for break-glass, IfExists only where absence must not deny (RCP org ID, service principal). Partial: correct results but by enumerating cases instead of conditions. Zero: exemptions by account id or wildcard role names that also exempt developers. |
| 3 | Blast radius and placement | 10 | Model allow-list on Workloads and Sandbox only, VPC-endpoint rule on Prod only, region and audit rules on Root, FullAWSAccess untouched; RCP leaves AssumeRoleWithWebIdentity out so OIDC deploys keep working. |
| 4 | Policy hygiene | 5 | One concern per policy, readable Sids, no redundant statements, comfortably under the size limit. |
| 5 | ANSWER.md production view | 15 | Full: a rollout plan without lockout (attach to a test OU or one sandbox account first, confirm with the IAM policy simulator or a dry run, watch CloudTrail errorCode AccessDenied with "service control policy" for a week, then widen), break-glass controls (MFA, alarms on use), the limits of SCPs (management account, service-linked roles, they grant nothing), keeping the global-service list and the inference-profile destination regions current as AWS changes them. Partial: generic. Zero: missing. |
Total: 100
