# Design: LFG help desk multi-region resiliency and DR runbook

<!-- Audience: CIO staff, security architecture, CAB. 4-8 pages equivalent. Use the inputs/ folder.
Be specific: name Connect features, quotas, and who does what. Diagrams in ```text or ```mermaid. -->

## Context and requirements

<!-- Restate the RTO/RPO per channel, scope, and what is explicitly out of scope. -->

## Target architecture

<!-- Diagram: both regions, instance and replica, traffic distribution group(s), numbers, agents,
Lambdas, Lex, data stores, S3/KMS, ServiceNow, Okta. Active/standby or active/active, and why. -->

## Telephony and number strategy

<!-- How numbers follow the failover, what happens to the two unported DIDs, Avaya coexistence. -->

## Agents, identity and the desktop

<!-- How agents log in during and after failover (SAML, sign-in endpoint), the embedded CCP,
offshore/nearshore teams, agent distribution percentages. -->

## Regional dependencies and parity

<!-- For each dependency: what must exist in us-west-2, how it is deployed and kept in sync
(names, ARNs, $.AwsRegion), data replication, KMS, ServiceNow allow list, quotas. -->

## Chat and digital channels

<!-- How the widget/API endpoint moves, what the employee sees. -->

## Data, recordings and reporting continuity

<!-- RPO for CTRs, recordings, transcripts, analytics; what is lost or delayed. -->

## Failover decision and runbook

<!-- Triggers, decision owner, step-by-step runbook with commands/console steps and timings,
verification, communications, failback. -->

## Testing and game days

<!-- Drill plan, success criteria, synthetic tests, how often. -->

## Cost and operational overhead

<!-- What the warm secondary costs and why; how to answer the CFO. -->

## Risks and open questions
