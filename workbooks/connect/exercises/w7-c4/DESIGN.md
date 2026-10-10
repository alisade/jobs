# Design: CRM/ITSM integration for LFG on Amazon Connect (ServiceNow + Salesforce)

<!-- Deliverable for connect/w7-c4. Write for LFG's architecture review board: a decision they can sign.
Use inputs/current-state.md and inputs/requirements.md. Cite AWS/vendor docs where a capability matters.
ASCII diagrams or mermaid are fine. Aim for 1,500-2,500 words. -->

## Context and requirements

<!-- Restate the problem and the requirements that drive the decision (reference R1-R10). -->

## Options considered

<!-- For ServiceNow (IT) and Salesforce (People Desk) separately: the realistic integration options,
who owns the Connect instance in each, what each gives you out of the box, and a scored comparison
table against the requirements. Be precise about Amazon Connect CTI Adapter for Salesforce vs
Salesforce Service Cloud Voice (bundle vs partner telephony / bring your own Amazon Connect), and about
what AWS documents for ServiceNow vs what ServiceNow itself provides. -->

## Recommended architecture

<!-- Diagram plus a walkthrough of one IT call and one People Desk call end to end. -->

## Screen pop and context passing

<!-- What data, from where, at what moment (flow attributes, Lambda lookups, Customer Profiles,
agent workspace app or CRM-embedded softphone). -->

## Contact and ticket logging

<!-- How R2 and R4 are met: data model on each side, idempotency key, event source (EventBridge contact
events, contact records, Contact Lens), retry and failure handling, 7-year traceability. -->

## Identity, access and security

<!-- SSO for Connect and each CRM, RBAC/ABAC for two business units on one instance, PII rules (R9). -->

## Operations, ownership and cost

<!-- Who runs what after hypercare (R10), release and upgrade dependencies (managed package versions,
ServiceNow family upgrades), licensing and billing implications. -->

## Risks and open questions

<!-- Top risks with mitigations; questions you need answered before build. -->

## Decision record

<!-- ADR style: decision, status, consequences. -->
