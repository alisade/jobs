# Design: ControlPilot production architecture and control-owner review pack

<!-- Audience: the audit committee's IT advisor, the CISO's architecture review and the external
auditor's IT specialist. 5-8 pages equivalent. Use inputs/. Be specific: name services, identities,
data stores, retention settings and who approves what. Diagrams in ```text or ```mermaid. -->

## Context and requirements

<!-- Restate the committee conditions and security standards you must meet; what is out of scope. -->

## Architecture overview

<!-- Diagram: Azure hosting (compute, orchestration, storage), the model on Gemini Enterprise Agent
Platform, enterprise systems (GitHub, ServiceDesk, GRC Hub, Entra ID), reviewers. Why each choice. -->

## Execution model: orchestration, state and review checkpoints

<!-- How a test run proceeds per sample: durable orchestration, checkpoints, retries without
duplicate side effects, where it pauses for a human, preparer/reviewer separation, kill switch. -->

## Identity, access and tool scoping

<!-- Managed identities, Workload Identity Federation from Azure to Google (no keys), per-tool
permissions, read vs write tools, approval for writes, engagement scoping. -->

## Data flow, residency and retention

<!-- Where evidence, prompts, responses, workpapers and logs live; regions; immutability and 7-year
retention; PII handling; what the model provider sees and keeps. -->

## Traceability: evidence citations and the execution log

<!-- What is logged per step and per model call, how a workpaper conclusion links to evidence,
how an external auditor re-performs an item. -->

## Evaluation, monitoring and change management

<!-- Evals per control in CI, quarterly metrics, production monitoring and alerting, and how a
change to code, prompt, model version or tool permissions goes through CM-03 itself. -->

## Threat model

<!-- Prompt injection through evidence, the lethal trifecta, data exfiltration paths, privilege
escalation through tools, model outage; mitigations and residual risk. -->

## Cost model

<!-- Per item and per year from inputs/volumes, the drivers, and what you would do to reduce it. -->

## Risks, open questions and rollout plan

<!-- What you would pilot first, exit criteria for each phase, decisions you need from the committee. -->
