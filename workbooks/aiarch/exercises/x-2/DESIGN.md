# ADR-007: How Lighthouse deploys to AWS, and how the agent VPC endpoints are locked down

<!-- Write this as the ADR you would put in front of the architecture review. About 900-1500 words.
Use inputs/requirements.md. Keep each section concrete: names, accounts, roles, policies. -->

## Context

<!-- The problem in a paragraph: what exists today, what the stakeholders want, what forces the decision. -->

## Options

<!-- At least: (A) GitLab-native cdk deploy with OIDC, (B) CDK Pipelines on CodePipeline sourced from
GitLab through CodeConnections, (C) a hybrid. For each: how a release flows, where approval happens,
where the audit trail lives, credentials, cost, effort. A comparison table helps. -->

## Decision

<!-- The option you pick and the two or three reasons that decide it. Name what you give up. -->

## Release flow

<!-- Diagram (text or mermaid) from merge request to prod endpoint, including the image digest,
approvals, the change window and rollback. -->

## Private networking and endpoint policies

<!-- Endpoint policy for bedrock-runtime and for bedrock-agentcore (JSON sketches), how the OAuth
bearer-token case is handled, how this interacts with the SCP on aws:SourceVpce, how you test it. -->

## Consequences and follow-ups

<!-- What changes for developers, security and audit; risks; what you will revisit and when. -->
