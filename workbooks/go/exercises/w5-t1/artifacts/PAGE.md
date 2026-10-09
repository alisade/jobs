# PagerDuty: [P2] agent.audit consumer lag SLO burn - audit-sink (prod-use1)

Triggered: 2026-10-06 14:21 UTC  Service: agent-platform / audit-sink  Escalation: platform-oncall

> Alert `KafkaConsumerLagBurnRate` firing for group `audit-sink` on topic `agent.audit`.
> Lag 412,880 and rising (SLO: lag < 50k for 99% of 5m windows). 6 partitions.

## Slack #agent-platform-incidents (excerpt)

**14:24 maria.k (compliance eng):** audit dashboard in OpenSearch is ~20 min behind and
some events show up 3 or 4 times. Auditors pull this tomorrow morning.

**14:26 dev.r (agent runtime):** we shipped PR #412 to audit-sink this afternoon
(static membership + smaller CPU limit, see `pr-412.diff`). ArgoCD synced 14:02. Rollout
looked clean, all 3 pods Ready.

**14:31 sam.t (SRE):** pods are Running but restart counts keep going up, and the HPA
scaled to 4 for a few minutes at 14:12. `kubectl top` shows them pinned at the CPU limit
and CFS throttling at ~38%. My bet is the new 500m limit: they are too slow, the group
kicks them out, they rejoin. Want to bump the limit back to 1 CPU and raise
`KAFKA_SESSION_TIMEOUT` to 5m?

**14:33 dev.r:** session timeout already went from 45s to 120s in #412 for the static
membership. Not sure more is better.

**14:35 you:** looking. Please do not change anything yet.

## What you have

Everything in this folder was captured between 14:30 and 14:45 UTC:

| path | what |
|---|---|
| `pr-412.diff` | the change that went out at 14:02 |
| `../deploy/audit-sink.yaml` | the manifest ArgoCD applied |
| `../internal/sink/` | consumer config and poll loop |
| `logs/` | container logs from the three pods (`kubectl logs --previous` where noted) |
| `kafka/` | MSK broker GroupCoordinator log excerpt, `kafka-consumer-groups.sh` output |
| `kubectl/` | pods, describe, events, top, HPA |
| `metrics/` | Prometheus query results |

You can also replay the incident locally against an in-process Kafka: `make repro`.
