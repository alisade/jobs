"""Generate incident evidence for aiarch/w3-t1 into incident/ (stdlib only)."""
import json
import sys
from pathlib import Path

out = Path(sys.argv[1] if len(sys.argv) > 1 else "incident")
out.mkdir(parents=True, exist_ok=True)
(out / "PAGE.txt").write_text("""INC-20451  P2  helpdesk agent v2.5.0 never becomes healthy on AgentCore Runtime (dev)
Opened 2026-11-13 09:12 by platform on-call (D. Brandt)

v2.5.0 is the first image built by GitLab CI; v2.4.x were built by hand on a developer
MacBook (Apple silicon) and pushed with docker push. The pipeline is green: build-image pushed
the tag, image-arch-gate is still a TODO script that the job allows to fail. CDK deploy to dev
updated the runtime, but the dev endpoint never reaches READY and invocations return 424/500.

On-call notes:
- 09:30 The /ping handler must be too slow; AgentCore gives up on health checks. Proposing a
  longer startup and a lighter /ping.
- 09:41 Container port is 8080, same as v2.4.x.
""")
(out / "job-9003114-build-image.log").write_text("""Running with gitlab-runner 18.5.1 (on gitlab-hosted saas-linux-small-amd64 abc123)
Executing "step_script" stage of the job script
$ docker build -t "${IMAGE}:${IMAGE_TAG}" .
#1 [internal] load build definition from Dockerfile
#4 [internal] load metadata for docker.io/library/python:3.12-slim
#5 [1/4] FROM docker.io/library/python:3.12-slim@sha256:2f8e...
#9 exporting to image
#9 writing image sha256:9d1c77... done
#9 naming to 111100000002.dkr.ecr.us-east-1.amazonaws.com/lighthouse/helpdesk-agent:v2.5.0 done
$ docker push "${IMAGE}:${IMAGE_TAG}"
v2.5.0: digest: sha256:41be0c... size: 1789
Job succeeded
""")
(out / "ecr-describe-images.json").write_text(json.dumps({"imageDetails": [
    {"imageTags": ["v2.4.1"], "imageDigest": "sha256:7aa0e1", "imageManifestMediaType": "application/vnd.oci.image.index.v1+json",
     "artifactMediaType": "application/vnd.oci.image.config.v1+json", "imagePushedAt": "2026-10-28T14:02:11Z", "imageSizeInBytes": 61833021},
    {"imageTags": ["v2.5.0"], "imageDigest": "sha256:41be0c", "imageManifestMediaType": "application/vnd.docker.distribution.manifest.v2+json",
     "artifactMediaType": "application/vnd.docker.container.image.v1+json", "imagePushedAt": "2026-11-13T08:51:40Z", "imageSizeInBytes": 60021777}]}, indent=1) + "\n")
(out / "imagetools-v2.4.1.txt").write_text("""Name:      111100000002.dkr.ecr.us-east-1.amazonaws.com/lighthouse/helpdesk-agent:v2.4.1
MediaType: application/vnd.oci.image.index.v1+json
Digest:    sha256:7aa0e1
Manifests:
  Name:      ...helpdesk-agent:v2.4.1@sha256:c01f
  MediaType: application/vnd.oci.image.manifest.v1+json
  Platform:  linux/arm64
""")
(out / "imagetools-v2.5.0.txt").write_text("""Name:      111100000002.dkr.ecr.us-east-1.amazonaws.com/lighthouse/helpdesk-agent:v2.5.0
MediaType: application/vnd.docker.distribution.manifest.v2+json
Digest:    sha256:41be0c
Image config: {"architecture":"amd64","os":"linux"}
""")
(out / "runtime-application-logs.txt").write_text("""2026-11-13T08:58:02Z runtime=lighthouse_helpdesk_dev version=12 session=- starting container
2026-11-13T08:58:03Z runtime=lighthouse_helpdesk_dev version=12 exec /usr/local/bin/python: exec format error
2026-11-13T08:58:03Z runtime=lighthouse_helpdesk_dev version=12 container exited with code 255
2026-11-13T08:58:09Z runtime=lighthouse_helpdesk_dev version=12 starting container
2026-11-13T08:58:09Z runtime=lighthouse_helpdesk_dev version=12 exec /usr/local/bin/python: exec format error
2026-11-13T08:58:40Z runtime=lighthouse_helpdesk_dev version=12 health check GET /ping failed: connection refused
""")
(out / "invoke-agent-runtime.txt").write_text("""$ aws bedrock-agentcore invoke-agent-runtime --agent-runtime-arn arn:aws:bedrock-agentcore:us-east-1:111100000003:runtime/lighthouse_helpdesk_dev-Q2w3E4r5T6 --qualifier dev ...
An error occurred (RuntimeClientError) when calling the InvokeAgentRuntime operation: Runtime initialization failed. Check your container logs.
""")
