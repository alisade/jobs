# ANSWER: aiarch/x-2

## Approach

Listed the hard constraints (in-AWS execution, named approver, MR feedback, cost) separately from
preferences, then scored each option against them; checked the endpoint policy limits for bearer
tokens in the AgentCore docs.

## Fix

Hybrid: GitLab for merge-request checks and image build, CDK Pipelines in shared-services for
deploys with a manual approval before prod. Endpoint policies scoped to the org for SigV4 and to
the runtime ARN for bearer-token calls.

## Trade-offs / what I would do in production

If audit insisted on GitLab as the only record, I would fall back to option A with protected
environments and CloudTrail session tags carrying the GitLab approver; migration is cheap because
both run the same CDK app.
