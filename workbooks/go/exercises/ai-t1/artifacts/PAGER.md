# Opsgenie: OG-40117 [P1] support-copilot: tool calls failing (agents/agent-runtime)

Opened: 2026-10-07 08:12 UTC  Cluster: eks-prod-use1-b  Reporter: synthetic check + #copilot-help

Alert: `agent_tool_call_errors_total{server="k8s-tools"} / agent_tool_calls_total > 0.5 for 10m`
(currently 100%)

> From #copilot-help, Jordan (SRE on-call for the agent platform):
> Every MCP call from agent-runtime to k8s-tools comes back `403 RBAC: access denied`
> since early this morning. The copilot still answers, but says it "cannot access the
> cluster tools". Nothing changed in agent-runtime or k8s-tools: both last deployed
> Friday. The mesh team did the Istio 1.25 -> 1.27 upgrade yesterday evening and said it
> went clean ("canary revision, then removed the old control plane").
> Karpenter consolidated the agents node pool at 06:40, so all agent-runtime pods were
> recreated around then.
>
> Also: EKS sent a notice that the cluster OIDC signing keys rotate this week. The MCP
> server validates projected SA tokens from that issuer - maybe that?

Platform standards: ADR-017 "Istio canary upgrades": namespaces opt in with the
`istio.io/rev=<revision>` label; we do NOT create a `default` revision tag, so a namespace
is only ever pinned to one explicit revision.
