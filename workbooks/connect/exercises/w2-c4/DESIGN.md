# LFG Help Desk Transformation - Solution Design Document

Author: <you>        Version: 0.1        Status: draft for design review

<!-- Write for two audiences: the steering committee (sections 1-3, 13-15) and the offshore build
team (sections 4-12). Use the numbers in inputs/. Keep each section tight: tables and bullets beat
prose. Diagrams in ```text or ```mermaid blocks. -->

## 1. Executive summary

<!-- 5-8 bullets: what we are building, why, the three biggest design decisions, the go-live path,
the headline outcomes and cost. -->

## 2. Current state and drivers

<!-- The few numbers that matter (volumes, SL, AHT, drivers, cost per contact) and the pain points
that the design must fix. -->

## 3. Requirements traceability and success metrics

<!-- Table: requirement id (B*, F*, N*) -> design element (section) -> how it is measured. -->

## 4. Target architecture

<!-- Logical architecture diagram and a component table (Connect instance(s), flows, Lex, Lambda,
ServiceNow, Okta, data lake, monitoring). Name the Connect features you use with current names. -->

## 5. Channels and journeys

<!-- Voice IVR, chat (portal-embedded), portal tickets, outbound notifications. One journey per top
driver: what is self-service, what goes to an agent, with what context. -->

## 6. Identity, verification and SSO

<!-- Employee identification (ANI, portal context), verification tiers and step-up, agent SSO
(SAML with Okta), admin access. -->

## 7. Routing and workforce design

<!-- Queues, routing profiles, proficiencies / routing criteria, VIP, languages, overflow, callbacks,
hours and holidays. Staffing estimate for the Monday peak (show the Erlang C inputs/outputs). -->

## 8. Integrations

<!-- ServiceNow (screen pop, incident create/lookup, work notes, knowledge), Okta, HR directory,
status page. Patterns, auth, idempotency, failure behavior. -->

## 9. AI and self-service

<!-- Lex bots, generative features, agent assist (AI agents / knowledge), after-contact summaries;
guardrails, evaluation, containment targets. -->

## 10. Analytics, quality and reporting

<!-- Conversational analytics (Contact Lens), evaluation forms, dashboards, contact-record data lake,
KPI definitions. -->

## 11. Security, privacy and compliance

<!-- Data classification, redaction, encryption, retention (N4), audit, least privilege, residency. -->

## 12. Resiliency and operations

<!-- Availability targets, multi-Region design (Connect Global Resiliency), DR runbook outline,
monitoring and alarms, runbooks, support model. -->

## 13. Delivery plan, migration and cutover

<!-- Phases and timeline within 4 months, environments and CI/CD, migration waves off Avaya/Genesys,
number porting, parallel run, rollback, test strategy, hypercare. RACI with the offshore team. -->

## 14. Risks, assumptions and decisions

<!-- Top risks with mitigations; architecture decision records (decision, options, rationale). -->

## 15. Cost model

<!-- Monthly run cost estimate by component with stated assumptions; cost per contact vs today. -->
