# go/w5-t1 ANSWER (model)

## Approach

Started from the page, then checked whether the group was actually rebalancing or
something else. `consumer-groups-describe.txt` shows `#MEMBERS 1` with a single consumer
owning `agent.audit(0,1,2,3,4,5)` while three pods are Ready, so two pods were not in the
group at all. That pointed at membership, not throughput. Then read the broker log and
pod logs around the restarts, the manifest and `FromEnv`, and confirmed with `make repro`.

## Root cause

All replicas use the same static member id. The Deployment sets
`GROUP_INSTANCE_ID: audit-sink` as a literal (and `FromEnv` would default to the constant
`audit-sink-0`). The coordinator keeps one member per instance id, so each join replaces
the previous holder and fences it:

- broker: `Static member with groupInstanceId=audit-sink and unknown member id joins group
  audit-sink in Stable state. Replacing previously mapped member audit-sink-... with this
  groupInstanceId.` followed by `... is fenced`
- pods: `heartbeat errored ... FENCED_INSTANCE_ID` then `fatal: fenced, exiting so the
  kubelet restarts us`; describe pod `Last State: Terminated, Exit Code: 1`, restart count 10
  on every pod; `GROUP_INSTANCE_ID: audit-sink` in every pod's environment
- group: `#MEMBERS 1`, one consumer owns all 6 partitions; offsets moved backwards after a
  handover; processed/produced = 1.31 (duplicates in OpenSearch)
- `make repro` with the shipped manifest: one pod `assigned [0 1 2 3 4 5]` at a time,
  repeated `exit 1: ... FENCED_INSTANCE_ID`, processed 18000 of 6000 preloaded.

CPU throttling is a symptom: only the current owner (t2r9w, 487m, 38% throttled) works;
the other pods sit at 9-12m. The HPA scale-out added a fourth pod with the same id, which
made it worse. A longer session timeout would not touch fencing and would make a dead
static member's partitions stall longer.

## Fix

- `deploy/audit-sink.yaml`: StatefulSet + headless Service, `GROUP_INSTANCE_ID` from
  `fieldRef: metadata.name` (audit-sink-0..2, stable across restarts and rollouts), HPA
  retargeted to the StatefulSet, PDB kept, static membership kept.
- `internal/sink/config.go`: id from `GROUP_INSTANCE_ID`, else `POD_NAME`, else an error.
- Verified: `make repro` now shows three members with two partitions each, 0 fenced exits,
  0 restarts, processed == preloaded; `make test` passes.

## Trade-offs / what I would do in production

- Deployment + `metadata.name` would stop fencing but ids change each rollout; departed
  static members keep partitions until the 120s session timeout: a lag spike every deploy.
- Migration: apply the StatefulSet, delete the Deployment; the old `audit-sink` member
  expires after the session timeout (or remove it with an admin LeaveGroup).
- Make indexing idempotent on event id; report the duplicate window to compliance.
- Alert on group members < replicas and on processed/produced > 1.
