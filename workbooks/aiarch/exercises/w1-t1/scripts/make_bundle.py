"""Generate the incident evidence for aiarch/w1-t1 into incident/ (stdlib only)."""
import json
import sys
from pathlib import Path

out = Path(sys.argv[1] if len(sys.argv) > 1 else "incident")
out.mkdir(parents=True, exist_ok=True)
base = {"iss": "https://gitlab.com", "aud": "https://gitlab.com", "namespace_path": "harborpoint/lighthouse",
        "project_path": "harborpoint/lighthouse/platform", "project_id": "48151623", "user_login": "rel-bot",
        "pipeline_source": "push", "runner_environment": "gitlab-hosted", "iat": 1794729600, "exp": 1794733200}
main = dict(base, sub="project_path:harborpoint/lighthouse/platform:ref_type:branch:ref:main", ref="main",
            ref_type="branch", ref_protected="true", pipeline_id="1290441", job_id="8842107", environment="dev")
tag = dict(base, sub="project_path:harborpoint/lighthouse/platform:ref_type:tag:ref:v2.4.0", ref="v2.4.0",
           ref_type="tag", ref_protected="true", pipeline_id="1290518", job_id="8842390", environment="production",
           environment_protected="true")
(out / "claims-main-deploy-dev.json").write_text(json.dumps(main, indent=1) + "\n")
(out / "claims-tag-v2.4.0-deploy-prod.json").write_text(json.dumps(tag, indent=1) + "\n")
(out / "PAGE.txt").write_text("""INC-20417  P2  Lighthouse release v2.4.0 cannot deploy to prod
Opened 2026-11-12 16:05 by release manager (S. Okafor)

The first release since we switched to tag-based releases (CHG-8812, approved 2026-11-05:
"main deploys to dev automatically; prod deploys only from protected release tags vX.Y.Z,
manual, through the production environment"). Pipeline 1290518 for tag v2.4.0: unit and synth
are green, deploy-prod fails in before_script with AccessDenied from STS. deploy-dev on main
(pipeline 1290441) still works with the same .aws-oidc template.

On-call notes:
- 16:20 (D. Brandt) GitLab rotated their TLS certificate chain last month. The OIDC provider
  in prod still has the old thumbprint. Probably this. Opening a change to update it.
- 16:31 (D. Brandt) Prod deploy role identity policy unchanged since September.
- 16:40 Nobody has touched trust/ since CHG-7730 (August), when prod deployed from main.
""")
(out / "job-8842390-deploy-prod.log").write_text("""Running with gitlab-runner 18.5.1 (on gitlab-hosted saas-linux-small-amd64)
Preparing environment
Getting source from Git repository
Fetching changes with git depth set to 20...
Checking out 5e1c0a9d as detached HEAD (ref is v2.4.0)...
Downloading artifacts for synth (8842388)...
Executing "step_script" stage of the job script
$ export $(printf "AWS_ACCESS_KEY_ID=%s ..." $(aws sts assume-role-with-web-identity --role-arn "${DEPLOY_ROLE_ARN}" ...))
An error occurred (AccessDenied) when calling the AssumeRoleWithWebIdentity operation: Not authorized to perform sts:AssumeRoleWithWebIdentity
ERROR: Job failed: exit code 254
""")
event = {
    "eventVersion": "1.09", "eventTime": "2026-11-12T16:02:41Z", "eventSource": "sts.amazonaws.com",
    "eventName": "AssumeRoleWithWebIdentity", "awsRegion": "us-east-1", "sourceIPAddress": "34.74.90.68",
    "userAgent": "aws-cli/2.31.4 md/Botocore#1.40.4 ua/2.1 os/linux#6.8 md/arch#x86_64",
    "userIdentity": {"type": "WebIdentityUser", "principalId": "arn:aws:iam::111100000004:oidc-provider/gitlab.com:https://gitlab.com:project_path:harborpoint/lighthouse/platform:ref_type:tag:ref:v2.4.0",
                     "userName": "project_path:harborpoint/lighthouse/platform:ref_type:tag:ref:v2.4.0",
                     "identityProvider": "arn:aws:iam::111100000004:oidc-provider/gitlab.com"},
    "errorCode": "AccessDenied", "errorMessage": "An unknown error occurred",
    "requestParameters": {"roleArn": "arn:aws:iam::111100000004:role/gitlab-deploy-prod",
                          "roleSessionName": "gitlab-48151623-1290518", "durationSeconds": 3600},
    "responseElements": None, "recipientAccountId": "111100000004", "eventType": "AwsApiCall",
}
(out / "cloudtrail-assume-role-with-web-identity.json").write_text(json.dumps({"Records": [event]}, indent=1) + "\n")
(out / "oidc-provider-prod.json").write_text(json.dumps({
    "Url": "gitlab.com", "ClientIDList": ["https://gitlab.com"],
    "ThumbprintList": ["b3dd7606d2b5a8b4a13771dbecc9ee1cecafa38a"],
    "CreateDate": "2025-08-02T10:11:12Z",
    "Note": "exported with aws iam get-open-id-connect-provider; AWS secures communication with well-known IdPs using its own trusted CA library, so the thumbprint is not used for gitlab.com"}, indent=1) + "\n")
