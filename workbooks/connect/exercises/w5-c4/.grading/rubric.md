# Rubric: connect/w5-c4 AI-assisted help desk design
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0). Use the completeness report only to spot empty sections. |
| 2 | Use-case scoping and metrics | 10 | Full: drivers mapped to deterministic self-service vs RAG vs agent assist with reasons; baselines from the inputs; containment defined with a repeat-contact guard; phase targets. Partial: generic "deflect 40%". |
| 3 | Architecture correctness | 15 | Full: components and data flow are right and current (Lex V2 in flows, Lambda sync 8 s / async 60 s, Bedrock Retrieve + Converse or QnAIntent with filters, Guardrails, AI agents formerly Q in Connect, Contact Lens summaries, ServiceNow via API), managed vs custom pieces named, regions and residency. Zero credit for invented features or a native "Bedrock flow block". |
| 4 | Handoff and agent experience | 15 | Full: explicit handoff contract (attributes, summary), copied into contact attributes, shown in the workspace view/screen pop and written to ServiceNow; agent assist and post-contact summary with human review. Partial: "pass context" without a contract. |
| 5 | Knowledge, entitlements and safety | 20 | Full: source of truth and sync, managed vs customer-managed KB trade-off (ServiceNow connector ACL crawl, RetrieveAndGenerate not on managed KBs), entitlement filters from authenticated attributes, retired content, guardrail policies with thresholds, prompt injection from speech and documents, invocation logs as sensitive data, retention 13 months. Partial: guardrails named without policy choices. |
| 6 | Latency and evaluation | 15 | Full: per-turn budget arithmetic under 8 s with fallback (async mode, holding prompt, handoff); eval plan with offline sets, red team, entitlement probes, gates, shadow/percentage rollout, owners and cadence. Partial: one of the two. |
| 7 | Cost model | 15 | Full: per-contact costs for contained and handled contacts by channel from the inputs, monthly totals and savings, sensitivity showing what drives the case, prices flagged as illustrative and to be verified. Partial: token costs only. Zero: no numbers. |
| 8 | Delivery and decisions | 10 | Full: phased plan in 16 weeks with flags/rollback, monitoring and runbooks, RACI with the offshore/nearshore teams, ADR-style decisions and risks. Partial: phases only. |
Total: 100
