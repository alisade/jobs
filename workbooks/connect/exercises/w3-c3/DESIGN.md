# DESIGN: LFG hybrid coexistence and number porting cutover plan

<!-- Audience: LFG CIO staff, telephony team, offshore NOC leads, AWS account team.
Use inputs/number-inventory.csv, inputs/current-state.md and inputs/constraints.md.
Ground every Connect / Voice Connector capability in AWS documentation; do not invent a
"Connect SIP trunk". Diagrams can be ASCII or mermaid. -->

## 1. Context, goals and non-goals

<!-- What problem, which numbers and platforms are in scope, what success looks like. -->

## 2. Number inventory analysis

<!-- Group the inventory into port tickets (per carrier and country) and waves. Call out
numbers that do not move, that need special handling (UK, Canada, Chime SDK hotline, Five9
caller ID), and which are on the critical path. -->

## 3. Coexistence architecture

<!-- Diagram. Which platform is primary for each number range in each wave; how calls cross
between Avaya/Genesys and Connect (forwarding, transfers over the PSTN, the Voice Connector
trunk's role and limits); how recordings/analytics cover Avaya calls (constraint 6). -->

## 4. Context passing between platforms

<!-- How the employee ID and ServiceNow incident travel with a transfer in both directions,
given what Connect does and does not accept over the PSTN. -->

## 5. Porting plan

<!-- Tickets, documents (LOA), lead times per country, request windows, sequencing against the
waves and freezes, testing before port dates, what you ask AWS and each carrier for. -->

## 6. Cutover runbook

<!-- Timeline from T-30 days to T+7 days for one port event (pick the 1-800 help desk number).
Who does what, go/no-go criteria, validation calls, communications. -->

## 7. Parallel run and validation

<!-- How long, what you compare (call paths, KPIs, recordings), exit criteria. -->

## 8. Rollback plan

<!-- Before the port, during the port window, after the port. What "rollback" can and cannot
mean once a number has moved. -->

## 9. Risks and mitigations

<!-- Top risks with owner and mitigation. -->

## 10. RACI and communications

<!-- LFG telephony, Pune NOC, Monterrey, carriers, AWS, ServiceNow team, service desk. -->

## 11. Open questions and decisions needed
