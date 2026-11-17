# Reference: aiarch/w6-t1

Root cause: in a CDK deploy CloudFormation calls IAM as the bootstrap cfn-exec role; the SCP
exempts only `gitlab-deploy-*`. Fix: exempt `role/cdk-hnb659fds-cfn-exec-role-*` (and
break-glass), drop the GitLab exemption. "Explicit deny in a service control policy" rules out
the boundary, which would be an implicit deny.
