# go/w5-t1 audit-sink rebalances in a loop after "static membership" rollout

**Type:** troubleshooting | **Estimate:** 2 hours | **Week 5:** Prometheus/OTel, Istio/Envoy, Kafka with franz-go (Fri Kafka from Go)

## Scenario

RelayPoint's `audit-sink` consumes `agent.audit` (6 partitions, ~4k records/s) on EKS
and indexes every agent action into OpenSearch for compliance. Forty minutes after PR
#412 synced, the lag SLO is burning, the audit dashboard is 20 minutes behind and
some events appear several times. The pods are Running and Ready, restart counts are
climbing, and the on-call SRE wants to raise the CPU limit and the session timeout.

Start with `artifacts/PAGE.md`. Everything you need is in `artifacts/`, `deploy/` and
`internal/sink/`. `make repro` replays the incident against an in-process Kafka
(franz-go `kfake`) using the replicas rendered from `deploy/audit-sink.yaml`.

## Task

1. Find the root cause. There is one primary cause; the page contains a plausible
   theory that is not it.
2. Fix it in the repo (manifest and/or Go code) without giving up what PR #412 was trying
   to achieve: rolling deploys and pod restarts must not trigger a full group rebalance.
3. Write `ANSWER.md` with the root cause and the evidence that proves it (quote the
   artifact lines), what you changed, and how you verified it.

## Acceptance criteria

- `make repro` shows every replica owning partitions, no `FENCED_INSTANCE_ID`, no restarts,
  and no records processed twice.
- The fixed manifest still parses as valid Kubernetes objects; the HPA and PDB still point
  at the workload; static membership is still on.
- The Go config cannot silently give two replicas the same identity again.
- `make test` passes. Hidden tests check the manifest, the config and a kfake run.

## How to run

```
make setup     # build; nothing to start, Kafka runs in-process
make repro     # replay the incident (~15s)
make test      # visible tests
```

## What to submit

Your edits under `deploy/` and `internal/` and your `ANSWER.md`, then `/grade go/w5-t1`
from the workbooks root.

## Study-guide links

- franz-go (kgo options incl. `InstanceID`): https://github.com/twmb/franz-go
- Kafka documentation: Design: https://kafka.apache.org/documentation/#design
- Amazon MSK: https://docs.aws.amazon.com/msk/latest/developerguide/what-is-msk.html
- KIP-345 static membership: https://cwiki.apache.org/confluence/display/KAFKA/KIP-345%3A+Introduce+static+membership+protocol+to+reduce+consumer+rebalances
- Kubernetes downward API: https://kubernetes.io/docs/concepts/workloads/pods/downward-api/
