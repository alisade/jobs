# Reference: aiarch/w1-c1

Reference policies are in `.grading/solution/policies/`. Key points:

- **Region guardrail in three statements.** Statement 1 is the classic region deny with a
  `NotAction` list of global services, and it also lists `bedrock:InvokeModel*` so Bedrock is
  handled separately. Statement 2 denies Bedrock invocation outside the three US
  cross-Region inference destinations. Statement 3 denies Bedrock in `us-west-2` unless
  `bedrock:InferenceProfileArn` is like `.../inference-profile/us.*`. `StringNotLike` on a key
  that is absent (a direct call without a profile) evaluates to true, so the direct call is
  denied: that is the behavior you want, and the reason to understand missing-key semantics.
- **Break-glass** is `ArnNotLike aws:PrincipalArn arn:aws:iam::*:role/hpm-breakglass`. A role of
  the same name in an outside account is still caught by the RCP, because RCPs key on
  `aws:PrincipalOrgID`, not on the role name.
- **Model allow-list** uses `NotResource` with foundation-model and inference-profile ARN
  patterns, attached to Workloads and Sandbox. Attaching it at Root would also bind the
  security and infrastructure accounts for no reason and make exceptions harder.
- **Prod private access** denies when `aws:SourceVpce` is not one of the two endpoints; the key is
  absent on public-endpoint calls, so the negated operator denies them.
- **RCP** uses `StringNotEqualsIfExists aws:PrincipalOrgID` plus
  `BoolIfExists aws:PrincipalIsAWSService false`, with `Principal "*"`, on
  `s3:*`, `sts:AssumeRole`, `kms:*`, `secretsmanager:*`, `sqs:*`. `sts:*` would also cover
  `AssumeRoleWithWebIdentity`, and a GitLab OIDC token has no org ID, so every pipeline would
  fail to assume its deploy role. AWS's RCP examples call this out.

Production notes worth hearing in the answer: test on a sandbox OU first, use CloudTrail to
find `AccessDenied` events whose message names a service control policy, keep break-glass
use alarmed, and remember SCPs never apply to the management account or service-linked roles,
so the management account must stay empty of workloads.
