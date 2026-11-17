# platform/w4-c1 - AppDatabase composition function and readiness

**Type:** coding (Go) | **Estimate:** 2-3 hours | **Study plan:** Week 4 (Crossplane v2); Go thread from weeks 1-3

## Scenario

Today a Tessellate team that needs a PostgreSQL database files a ticket, and someone on the platform
team clicks a Cloud SQL instance together. Dana K. (platform lead) wants self-service on top of the
Terraform foundation: a Crossplane v2 API `AppDatabase` that a developer creates in the team
namespace through Git, and ArgoCD syncs.

In Crossplane v2 the composite resource (XR) is namespaced and developers create it directly.
Claims are a v1 compatibility feature and are not used for new APIs. The composition runs as a
pipeline of functions; each function returns the desired composed resources. The composed resources
are namespaced managed resources (MRs) from the Upbound GCP provider family, in the
`sql.gcp.m.upbound.io` API group.

You write the logic of that function step and of the composite reconcile loop, against a small
in-memory model of the API (no cluster needed). The real thing would be a function written with the
function SDK plus Crossplane's own XR controller; the decisions are the same.

## What you have

| Path | What it is |
|---|---|
| `fn/types.go` | the XR, Resource, Condition and Client types, `SameDesired`, `IsReady`, condition helpers (do not change) |
| `fn/fake.go` | `FakeClient`: an in-memory API that counts writes and plays the provider with `SetReady` (do not change) |
| `fn/compose.go` | `Compose(xr) Result` - TODO |
| `fn/reconcile.go` | `Reconcile(ctx, client, xr) (XR, error)` - TODO |
| `fn/compose_test.go` | visible tests (happy path) |

Example XR, as a developer would write it:

```yaml
apiVersion: platform.tessellate.example/v1alpha1
kind: AppDatabase
metadata:
  name: riq-scores
  namespace: team-riq
spec:
  size: medium          # small | medium | large
  version: postgres-16  # postgres-15 | postgres-16
  team: riq
  # region: us-east4               optional, default us-central1
  # deletionPolicy: Orphan         optional, default Delete
  # providerConfigRef:             optional override
  #   kind: ProviderConfig
  #   name: riq-sandbox
```

## Composition contract (`Compose`)

1. Validate, and on the first problem return `Result{Fatal: "<field path>: <what is wrong>"}` with no
   resources (never panic). Field paths: `metadata.namespace` (required: the XR is namespaced),
   `metadata.name`, `spec.team` (lower-case DNS label, 1-30 chars, starts with a letter), `spec.size`,
   `spec.version`, `spec.deletionPolicy` (`""`, `Delete`, `Orphan`), `spec.providerConfigRef.name`
   (required when the override is set) and `spec.providerConfigRef.kind` (`ProviderConfig`,
   `ClusterProviderConfig` or empty).
2. Desired resources, in this order:
   - `DatabaseInstance <xr>-pg`: forProvider `databaseVersion` (`POSTGRES_15`/`POSTGRES_16`), `tier`
     (small `db-custom-1-3840`, medium `db-custom-2-7680`, large `db-custom-4-15360`), `region`,
     `availabilityType` (`REGIONAL` for large, otherwise `ZONAL`).
   - size large only: `DatabaseInstance <xr>-pg-replica` with `databaseVersion`, `tier`, `region` and
     `masterInstanceName = <xr>-pg`.
   - `Database <xr>-db`: `instance = <xr>-pg`, `name` = the XR name with `-` replaced by `_`, `charset = UTF8`.
   - `User <xr>-user`: `instance = <xr>-pg`, `name = <xr>-app`, and `WriteConnectionSecretToRef`
     `<xr>-conn` (written in the MR's namespace, which is the XR's).
3. Every resource: `APIVersion = MRAPIVersion`, namespace = the XR namespace, labels exactly
   `crossplane.io/composite=<xr name>` and `platform.tessellate.example/team=<team>`, `DeletionPolicy`
   (default `Delete`), `ProviderConfigRef` = `{ClusterProviderConfig, default}` unless the XR overrides
   it; an override without a kind means `ClusterProviderConfig`.

## Reconcile contract (`Reconcile`)

- Fatal compose result: set `Synced=False` and `Ready=False`, reason `ComposeFailed`, message = the
  fatal text; write the XR status; return a nil error (bad input is not retried); do not touch MRs.
- List the composed resources by the composite label, in the XR namespace only.
- Apply a desired resource only when it is missing or differs (`SameDesired`). A second reconcile of
  an unchanged XR must issue zero Apply/Delete calls.
- Delete composed resources that are no longer desired (for example the replica after large to medium).
- `Synced=True` reason `ReconcileSuccess`. `Ready=True` reason `Available` only when every desired
  resource exists and is Ready; otherwise `Ready=False`, reason `Creating`, message
  `waiting for: Kind/name, Kind/name` in desired order.
- A client error: `Synced=False` reason `ReconcileError` with the error text, write the status, and
  return the error so the controller requeues.

## Acceptance criteria

- `make test` passes; the hidden suite covers invalid input, overrides, large/replica, idempotency,
  partial readiness, pruning, namespace scoping and client errors. Tests run with `-race`.
- `ANSWER.md` covers: why the XR is namespaced and there is no claim; why the default is a
  ClusterProviderConfig and what a team-scoped ProviderConfig would buy; what happens to the Cloud SQL
  instance when a developer deletes the XR under `Delete` vs `Orphan`, and what you would do for prod.

## How to run

```bash
make setup
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade platform/w4-c1
make clean
```

## What to submit

`fn/compose.go`, `fn/reconcile.go` and `ANSWER.md`.
