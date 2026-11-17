# ANSWER: aiarch/w3-t1

## Approach

Read the page, then compared the ECR records and imagetools output for v2.4.1 and v2.5.0, then
the Runtime logs and the build job log.

## Root cause

v2.5.0 is a linux/amd64 image and AgentCore Runtime only runs linux/arm64. The build job runs
on `saas-linux-small-amd64` with a plain `docker build`, which builds for the runner's own
architecture (`imagetools-v2.5.0.txt`: config architecture amd64; ECR shows a single Docker v2
manifest). The container's first exec fails: `exec /usr/local/bin/python: exec format error`
and exit 255 in the Runtime logs, so nothing listens on 8080 and the health check gets
connection refused. v2.4.x worked because they were built on Apple silicon laptops, which
produce arm64 natively (the v2.4.1 index lists linux/arm64). The gate that should have caught
it was a TODO and the job did not block.

The `/ping` theory is wrong: the process never started, so health check timing is irrelevant.

## Fix

Install binfmt/QEMU, `docker buildx build --platform linux/arm64 --provenance=false --push` with
the release tag, publish the raw manifest and the image config as artifacts, and run the gate on
both. The gate exits 0 for arm64, 1 for other platforms, 2 for unreadable input, and skips
attestation entries. Verified with `make gate` and `make test`.

## Trade-offs / what I would do in production

- QEMU builds are slow for heavy dependencies; an ARM runner (GitLab hosted ARM or a
  self-managed runner on CodeBuild ARM) is faster and avoids emulation bugs.
- Keep the image arm64-only unless something else needs amd64; a multi-arch index doubles
  build time.
- Scan in ECR on push and deploy by digest so the gate and the deploy see the same image.
