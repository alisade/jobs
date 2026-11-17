"""Generate incident evidence for aiarch/w6-t1 into incident/ (stdlib only)."""
import json
import sys
from pathlib import Path

out = Path(sys.argv[1] if len(sys.argv) > 1 else "incident")
out.mkdir(parents=True, exist_ok=True)
(out / "PAGE.txt").write_text("""CHG-8841 rollback  Lighthouse 2.6.0 prod deploy failed, stack rolled back
Opened 2026-11-14 15:20 by release manager (S. Okafor)

deploy-prod for tag v2.6.0 ran `cdk deploy` with the gitlab-deploy-prod role. The
LighthouseRuntime-prod stack went to UPDATE_ROLLBACK_COMPLETE. 2.6.0 adds a second runtime
role for the new MCP server target. Dev deployed fine on 2026-11-12, BEFORE security attached
the new SCP scp-iam-change-control to the Workloads OU (2026-11-13, SEC-3110: "only pipelines
may change IAM in workload accounts").

On-call notes:
- 15:35 (D. Brandt) gitlab-deploy-prod has a permissions boundary (hpm-pipeline-boundary).
  The boundary probably does not include iam:CreateRole. Opening a change to widen it.
- 15:42 The SCP exempts gitlab-deploy-*, and we deploy with gitlab-deploy-prod, so the SCP
  cannot be it.
""")
(out / "cloudformation-events.txt").write_text("""2026-11-14T15:11:02Z LighthouseRuntime-prod  UPDATE_IN_PROGRESS  User Initiated
2026-11-14T15:11:09Z McpServerRoleA1B2C3D4   CREATE_IN_PROGRESS
2026-11-14T15:11:10Z McpServerRoleA1B2C3D4   CREATE_FAILED  Resource handler returned message: "User: arn:aws:sts::111100000004:assumed-role/cdk-hnb659fds-cfn-exec-role-111100000004-us-east-1/AWSCloudFormation is not authorized to perform: iam:CreateRole on resource: arn:aws:iam::111100000004:role/LighthouseRuntime-prod-McpServerRoleA1B2C3D4-9XyZ with an explicit deny in a service control policy (Service: Iam, Status Code: 403, Request ID: 6f1d2c3b-aaaa-bbbb-cccc-0123456789ab)"
2026-11-14T15:11:11Z LighthouseRuntime-prod  UPDATE_ROLLBACK_IN_PROGRESS
2026-11-14T15:13:40Z LighthouseRuntime-prod  UPDATE_ROLLBACK_COMPLETE
""")
ev = {"eventTime": "2026-11-14T15:11:10Z", "eventSource": "iam.amazonaws.com", "eventName": "CreateRole",
      "awsRegion": "us-east-1", "sourceIPAddress": "cloudformation.amazonaws.com", "userAgent": "cloudformation.amazonaws.com",
      "invokedBy": "cloudformation.amazonaws.com", "errorCode": "AccessDenied",
      "errorMessage": "User: arn:aws:sts::111100000004:assumed-role/cdk-hnb659fds-cfn-exec-role-111100000004-us-east-1/AWSCloudFormation is not authorized to perform: iam:CreateRole with an explicit deny in a service control policy",
      "userIdentity": {"type": "AssumedRole", "arn": "arn:aws:sts::111100000004:assumed-role/cdk-hnb659fds-cfn-exec-role-111100000004-us-east-1/AWSCloudFormation",
                       "sessionContext": {"sessionIssuer": {"type": "Role", "arn": "arn:aws:iam::111100000004:role/cdk-hnb659fds-cfn-exec-role-111100000004-us-east-1"}},
                       "invokedBy": "cloudformation.amazonaws.com"},
      "requestParameters": {"roleName": "LighthouseRuntime-prod-McpServerRoleA1B2C3D4-9XyZ"}, "recipientAccountId": "111100000004"}
(out / "cloudtrail-createrole.json").write_text(json.dumps({"Records": [ev]}, indent=1) + "\n")
(out / "assume-chain.txt").write_text("""GitLab job 9101877 (tag v2.6.0)
  AssumeRoleWithWebIdentity -> arn:aws:iam::111100000004:role/gitlab-deploy-prod
  cdk deploy: AssumeRole -> arn:aws:iam::111100000004:role/cdk-hnb659fds-deploy-role-111100000004-us-east-1
  CloudFormation UpdateStack with RoleARN arn:aws:iam::111100000004:role/cdk-hnb659fds-cfn-exec-role-111100000004-us-east-1
    (iam:PassRole by the deploy role; CloudFormation then makes every resource call as the exec role)
""")
(out / "gitlab-deploy-prod-boundary.json").write_text(json.dumps({"PolicyName": "hpm-pipeline-boundary",
    "Statement": [{"Effect": "Allow", "Action": ["sts:AssumeRole"], "Resource": "arn:aws:iam::111100000004:role/cdk-hnb659fds-*"}]}, indent=1) + "\n")
