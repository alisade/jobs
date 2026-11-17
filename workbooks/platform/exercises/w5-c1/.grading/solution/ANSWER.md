# ANSWER: platform/w5-c1 Admission gate for Helm-rendered manifests

## Approach

Wrote one traversal (`pod_template` + `all_containers`) and ran every rule over its output, then the
object-level rules (KSA, PDB). Tested the parser against helm's empty `---` documents first, then the
image parser with look-alike hosts. The spike's registry check used fnmatch over the full reference,
and fnmatch's `*` matches `/`, so `evil.example/us-docker.pkg.dev/tsl-artifacts-prod/x` passed; it now
matches the host on its own and checks the path prefix separately.

## Fix

Findings on the shipped render (dry-run, 5 violations):

- CronJob riq-reindex: `busybox:1.36` is from docker.io and pinned by tag (IMG001, IMG002). Owner: build
  a tiny reindex image through the prod pipeline, or call the endpoint from the riq-api image itself.
- StatefulSet rdm-worker: digest attested only by `qa-signoff` (IMG003); the image came from an rc
  build outside the prod pipeline. Rebuild through the pipeline so `prod-build-verified` signs it. Also 3
  replicas and no PDB (PDB001): add `maxUnavailable: 1`.
- ServiceAccount rdm-worker: token automount not disabled (WI002).

## Trade-offs / what I would do in production

The CI gate is early feedback; Binary Authorization stays the enforcement point because CI can be
bypassed. Keep Binary Authorization in dry-run until the audit log shows no unexpected would-deny
entries for a week, then enforce per cluster. Break-glass needs an incident number and an alert to
security from the Cloud Audit Logs entry. The attestation should be created by the build pipeline after
the Artifact Analysis vulnerability check, with SLSA provenance. The gate cannot see pods created by
operators or Helm hooks at runtime.
