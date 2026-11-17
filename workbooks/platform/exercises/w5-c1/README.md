# platform/w5-c1 - Admission gate for Helm-rendered manifests

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 5 (DevSecOps on GCP: Artifact Registry, Binary Authorization, GKE hardening)

## Scenario

Tessellate Systems runs MDM, RIQ and RDM on the prod-blue and prod-green GKE clusters. Binary
Authorization has been in dry-run on prod-blue for three weeks; the security team wants it in enforce
mode before the year-end freeze. Dana K. (platform lead) does not want the first signal of a bad image
to be a failed rollout at 2 AM: the same decisions must be made in CI, on the output of `helm template`,
so a chart change fails in its pull request.

A spike (PLAT-1201) left `gate.py` half written. The rules below are the security team's; the shipped
render in `rendered/` is what the three charts produce today.

## What you have

| Path | What it is |
|---|---|
| `gate.py` | the gate: library (`load_documents`, `load_paths`, `evaluate`) and CLI (`main`). Fill in the TODOs |
| `rendered/*.yaml` | `helm template` output for mdm-api, riq-api (Deployment with an init container, a CronJob) and rdm-worker (StatefulSet) |
| `config/policy.yaml` | required attestor, allowed registries, default namespace |
| `config/attestations.json` | export of attestations (the Binary Authorization stand-in): `resource_uri` (repo@digest), `digest`, `attestor` |
| `tests/` | visible tests |

## Rules

| Id | Rule |
|---|---|
| IMG001 | Image host matches an `allowed_registries[].host` glob (for example `*-docker.pkg.dev`) as a whole host, and the path starts with that entry's `path_prefix` (`tsl-artifacts-prod/`). `evil.example/us-docker.pkg.dev/...` is not Artifact Registry |
| IMG002 | Pinned by `@sha256:<64 hex>`. `repo:tag@sha256:...` is pinned (the digest wins); a tag alone is not |
| IMG003 | The digest has an attestation by `required_attestor` whose `resource_uri` (without `@digest`) equals the image repository (host/path, no tag). Only checked when IMG002 passes |
| SEC001 | `runAsNonRoot: true`, from the container or inherited from the pod `securityContext`; the container value wins |
| SEC002 | not `privileged` |
| SEC003 | `allowPrivilegeEscalation: false` |
| SEC004 | `readOnlyRootFilesystem: true` |
| SEC005 | `capabilities.drop` includes `ALL` |
| RES001 | `requests.cpu`, `requests.memory` and `limits.memory` (no CPU limit required, on purpose) |
| PRB001 | every app container of a Deployment has a `readinessProbe` (not init containers) |
| PDB001 | a Deployment or StatefulSet with `replicas > 1` has a PodDisruptionBudget in the same namespace whose `matchLabels` all match the pod template labels |
| WI001 | the pod runs as a dedicated KSA (not `default`) that is in the render and carries `iam.gke.io/gcp-service-account: <name>@<project>.iam.gserviceaccount.com` |
| WI002 | a ServiceAccount sets `automountServiceAccountToken: false` unless annotated `tessellate.example/needs-kube-api: "true"`; a pod spec must not set `automountServiceAccountToken: true` |

Every container counts: `initContainers`, `containers` and `ephemeralContainers` (ephemeral
containers have no resources, so RES001 does not apply to them). Pod templates live at
`spec.template` for Deployment, StatefulSet, DaemonSet, ReplicaSet and Job, at
`spec.jobTemplate.spec.template` for CronJob, and a bare Pod is its own template.

**Break-glass.** Like Binary Authorization, which reads `alpha.image-policy.k8s.io/break-glass: "true"`
from the Pod, the gate honours the annotation only on the pod template metadata (not on the Deployment's
own metadata). It waives IMG003 only, and each waived container appears in `exceptions` with rule, kind,
name, namespace, container, image and reason, so the security team can audit it.

## Your task

1. `load_documents`: skip empty and comment-only documents, expand `kind: List`, raise `GateError` on a
   document that is not a mapping or has no kind.
2. `pod_template` and `all_containers` for every workload kind and container field.
3. Review the spike's `registry_allowed` and `is_digest`; implement `attested`.
4. Implement the remaining rules in `evaluate`, including break-glass and `exceptions`.
5. CLI: `--mode dry-run` always exits 0, `--mode enforce` exits 1 on any violation, exit 2 on
   unparseable YAML or unreadable files. JSON output keeps the shape the starter prints.
6. In `ANSWER.md`: what the gate finds in the shipped render and what you would tell each chart owner,
   and how this CI gate and Binary Authorization at admission fit together.

## Acceptance criteria (what the grader checks)

- The shipped render gives exactly: IMG001 and IMG002 on CronJob riq-reindex, IMG003 and PDB001 on
  StatefulSet rdm-worker, WI002 on ServiceAccount rdm-worker. mdm-api is clean.
- Hidden tests: List kind, empty documents, CronJob template path, init containers, tag+digest, short
  digests, wrong attestor or repository, break-glass scope, look-alike hosts, other Artifact Registry
  regions, runAsNonRoot inheritance, PDB selector and namespace, Workload Identity rules, exit codes.
- Each finding has exactly the keys `rule, kind, name, namespace, container, message`.

## How to run

```bash
make setup
make run                 # dry-run over rendered/
make run MODE=enforce
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/w5-c1
make clean
```

## What to submit

`gate.py` and `ANSWER.md`. Do not change the tests or the fixtures.
