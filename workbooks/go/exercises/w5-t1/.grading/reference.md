# Reference: go/w5-t1 audit-sink rebalance loop

## Root cause

PR #412 enabled KIP-345 static membership and set `GROUP_INSTANCE_ID: audit-sink` as a
literal in the Deployment, and `FromEnv` falls back to the constant `audit-sink-0`. All
three replicas therefore join as the **same static member**. The coordinator maps an
instance id to exactly one member id, so every join replaces the previous member
("Static member with groupInstanceId=audit-sink ... Replacing previously mapped member").
The replaced member is fenced on its next heartbeat/commit (`FENCED_INSTANCE_ID`),
`main` exits 1, the kubelet restarts it with back-off, it rejoins and fences whoever holds
the id now. At any moment one pod owns all six partitions (`#MEMBERS 1`, one consumer on
`agent.audit(0..5)`), it is the only busy pod (CPU at the limit, 38% throttling), and
uncommitted batches are re-delivered after every handover (processed/produced 1.31,
duplicates in OpenSearch, offsets moving backwards).

## Red herrings

- **CPU limit / throttling:** a consequence. One pod does three pods' work; the others idle
  at 9-12m CPU. More CPU would let the current owner go faster until the next fence.
- **HPA scale to 4 at 14:12:** another pod with the same id, so more fencing. Not a cause.
- **Raising the session timeout:** irrelevant to fencing, and with static members a longer
  timeout means a dead member's partitions stall for longer.

## Fix (in `.grading/solution/`)

- `deploy/audit-sink.yaml`: StatefulSet (+ headless Service) so pods are `audit-sink-0..2`,
  `GROUP_INSTANCE_ID` from `fieldRef: metadata.name`, HPA `scaleTargetRef` kind
  StatefulSet, PDB unchanged. Stable names are what make static membership useful: a
  restarted `audit-sink-1` reclaims its partitions without a rebalance.
- `internal/sink/config.go`: `GROUP_INSTANCE_ID`, else `POD_NAME`, else `ErrNoInstanceID`.
  Never a constant.
- Why not Deployment + `metadata.name`: ids are unique (no fencing) but change on every
  rollout; static members do not send LeaveGroup on shutdown, so the old members keep
  their partitions until `session.timeout` (120s) expires: a lag spike every deploy.

## Verification

`make repro` before: one pod owns `[0 1 2 3 4 5]`, repeated `FENCED_INSTANCE_ID` exits,
processed > preloaded. After: three members with two partitions each, no fencing, no
restarts, processed == preloaded. Hidden tests: config, manifest and a kfake run.

## Production follow-up

- Migration: delete the Deployment, apply the StatefulSet; the old `audit-sink` static
  member expires after 120s or is removed with an admin LeaveGroup by instance id.
- Idempotent indexing (OpenSearch `_id` = event id) so re-delivery cannot duplicate audit
  records; tell compliance which window may contain duplicates.
- Alerts: `kafka_consumergroup_members < replicas`, restart rate, processed/produced > 1.
- A unit test that renders the manifest and asserts unique ids (the hidden test is one).
