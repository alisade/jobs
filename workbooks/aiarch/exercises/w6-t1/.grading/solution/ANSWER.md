# ANSWER: aiarch/w6-t1

## Approach

Read the stack events and the CloudTrail record, then the assume chain, then the new SCP;
replayed the calls with `make sim`.

## Root cause

The denied `iam:CreateRole` was made by
`arn:aws:iam::111100000004:role/cdk-hnb659fds-cfn-exec-role-111100000004-us-east-1`
(CloudTrail `sessionContext.sessionIssuer.arn`, `invokedBy: cloudformation.amazonaws.com`).
In a CDK deploy, GitLab's role only assumes the CDK deploy role, which passes the
CloudFormation execution role to CloudFormation; CloudFormation then makes every resource call
as that exec role. `scp-iam-change-control` exempts `aws:PrincipalArn` `role/gitlab-deploy-*`,
which never calls IAM, so the exec role's call is denied ("explicit deny in a service control
policy"). Dev deployed on 11-12, before the SCP was attached on 11-13.

The boundary theory is wrong: a permissions boundary produces an implicit deny ("no
permissions boundary allows"), not an explicit deny in an SCP, and the boundary is on a role
that never makes the call.

## Fix

The exemption now names `arn:aws:iam::*:role/cdk-hnb659fds-cfn-exec-role-*` plus break-glass,
and no longer the GitLab roles. Verified with make sim and make test.

## Trade-offs / what I would do in production

- A role name is only a boundary if nobody else can create that name: the SCP itself stops
  non-pipeline principals from creating roles, which protects the pattern. A custom bootstrap
  qualifier makes the name less guessable.
- Add `aws:CalledVia cloudformation.amazonaws.com` style conditions where the service supports
  them, and require a permissions boundary on roles CloudFormation creates.
- Test SCP changes against a request table (as here) and on a test OU before attaching.
