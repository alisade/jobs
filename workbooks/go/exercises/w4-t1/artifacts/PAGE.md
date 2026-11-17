# PagerDuty: PLAT-PAGE-7731 (SEV-2)

**Service:** agent-platform / agent-fleet-operator
**Cluster:** eks-prod-use1-agents (EKS 1.37), 2,140 MCPServer objects across 96 namespaces
**Triggered:** 2026-10-07 02:14 UTC, re-triggered 06:40 UTC
**Alerts:**
- `KubeAPIServerLatencyHigh`: p99 PUT latency on the agents.example.dev group 1.9s (SLO 1s)
- `OperatorCPUThrottled`: agent-fleet-operator at its 2 CPU limit since the v0.3.1 rollout
- `ControllerWorkqueueGrowing`: `workqueue_adds_total{name="mcpserver"}` slope > 500/s

**Reporter (platform on-call, 02:31):**
> Started right after ArgoCD synced agent-fleet-operator v0.3.1 on Tuesday evening.
> Logs are full of "Waited for ... due to client-side throttling", so I raised the
> client QPS/Burst from 20/30 to 100/200 (INC-4412, shipped in the same image) and
> the throttling messages mostly went away, but apiserver latency got worse and the
> EKS control plane team pinged us about APF queueing in `workload-low`.
> Nobody changed any MCPServer spec overnight. Teams say their servers work fine;
> it is just the control plane that is on fire. Rolling back is blocked because
> v0.3.1 also carries the status field the portal now depends on.

**Ask:** find the root cause, fix it in the operator, and explain why the QPS change
did not help.

Files in this folder: `controller-logs.txt`, `operator-metrics.txt`,
`apiserver-metrics.txt`, `audit-excerpt.jsonl`, `mcpserver-github-tools.yaml`,
`apf-dump.txt`, `git-log.txt`.
