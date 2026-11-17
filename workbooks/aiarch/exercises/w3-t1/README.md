# aiarch/w3-t1 - Agent v2.5.0 never becomes healthy on AgentCore Runtime

**Type:** troubleshooting | **Estimate:** 1-1.5 hours | **Study plan:** Week 3 (Mon: Runtime contract and ARM64 images; Fri: troubleshooting Runtime)

## Symptom

v2.5.0 of the Lighthouse helpdesk agent is the first image built by GitLab CI instead of on a
developer laptop. The pipeline is green and the CDK deploy updated the dev runtime, but the
`dev` endpoint never reaches READY and every invocation fails with "Runtime initialization
failed". On-call thinks `/ping` is too slow and wants a longer startup. Read
`incident/PAGE.txt` first (created by `make setup`).

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the ticket and on-call notes |
| `incident/job-9003114-build-image.log` | the build job log |
| `incident/ecr-describe-images.json`, `incident/imagetools-*.txt` | what is in ECR for v2.4.1 and v2.5.0 |
| `incident/runtime-application-logs.txt`, `incident/invoke-agent-runtime.txt` | Runtime logs and the client error |
| `.gitlab-ci.yml`, `Dockerfile` | the build (edit these) |
| `scripts/check_image_arch.py` | the image architecture gate: still a TODO (implement it) |
| `agent/server.py` | the container's HTTP contract, `/ping` and `/invocations` on 8080 (works as shipped) |
| `tests/fixtures/` | manifests and image configs for testing the gate |

## Your task

1. Find the root cause from the evidence; explain why v2.4.x worked.
2. Fix the build so the image runs on AgentCore Runtime. Either use an ARM runner, or keep
   the x86 runner and build with `docker buildx --platform linux/arm64` under QEMU (binfmt).
   Keep the immutable release tag; never push `latest`.
3. Implement the gate `scripts/check_image_arch.py` (see its docstring for exit codes; ignore
   attestation entries in an index) and make the gate job blocking, with every file it reads
   published by the build job.
4. Write `ANSWER.md`: Approach, Root cause (with evidence), Fix and verification, Trade-offs.
   Say why the `/ping` theory is wrong.

## Acceptance criteria (what the grader checks)

- The gate's decisions on index, multi-arch, attestation and single-manifest fixtures.
- The build produces linux/arm64, no `latest`, the gate gets its inputs and is blocking.
- Dockerfile and server contract unchanged in substance (port 8080, non-root).
- `ANSWER.md` names the architecture mismatch with evidence.

## How to run

```bash
make setup     # evidence bundle + aiarch/.venv
make gate      # run your gate against the fixtures
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade aiarch/w3-t1
make clean
```

## What to submit

`.gitlab-ci.yml`, `Dockerfile` (if changed), `scripts/check_image_arch.py`, `ANSWER.md`.
