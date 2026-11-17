# Reference: aiarch/x-2

Either main option can pass; what matters is the reasoning. A strong answer usually lands on a
hybrid: GitLab stays the developer surface (MR pipelines run tests, synth and `cdk diff` as an MR
comment) while the deploy itself runs in AWS (CDK Pipelines sourced from GitLab via
CodeConnections, or a CodeBuild project triggered from GitLab) so security gets in-AWS execution
and a CodePipeline manual approval with a named IAM principal; audit's "one system" is met by
treating CodePipeline as the record of deploys and linking it from the GitLab deployment, or by
keeping GitLab protected-environment approvals and recording them in CloudTrail session tags.
Endpoint policies: SigV4 statements conditioned on aws:PrincipalOrgID with specific actions; for
bearer-token calls to InvokeAgentRuntime a statement with Principal "*" scoped by Resource to the
runtime ARN, because the endpoint cannot see a JWT caller as an IAM principal; the SCP on
aws:SourceVpce still binds IAM callers. Test with calls from inside and outside the VPC and
from a non-org principal. See solution/DESIGN.md.
