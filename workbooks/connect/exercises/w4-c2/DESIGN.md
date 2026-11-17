# LFG help desk migration program plan (Avaya / Genesys / Five9 / Cisco -> Amazon Connect)

<!-- Audience: LFG steering committee and the delivery team. Use the facts in inputs/.
Keep each section tight; tables beat prose. -->

## 1. Goals, scope and success criteria

<!-- What is in and out of scope, measurable success criteria (SL, abandon, containment,
decommission dates), and the hard dates that drive the plan. -->

## 2. Migration strategy and waves

<!-- Wave table: wave, what moves (numbers, flows, queues, channels, agents), why that order,
entry and exit criteria, target dates around blackouts and contract renewals. -->

## 3. Coexistence during migration

<!-- How calls, transfers and agents work while some numbers are on Avaya/Cisco and some on
Connect. Name the coexistence option (see the AWS Avaya migration guidance) and the telephony
path; what happens to transfers between platforms and to ServiceNow screen pops. -->

## 4. Build approach (migration factory)

<!-- How the offshore factory ports 62 vectors, 22 ICM scripts, 18 Five9 scripts and 14 Genesys
strategies: inventory, rationalisation (what NOT to migrate), translation, review, golden
call-path suites, definition of done. -->

## 5. Validation and testing

<!-- Migration validation (legacy vs Connect path suites), integration tests, UAT, load test,
accessibility, synthetic test calls, parallel run. Who runs what and the exit gates. -->

## 6. Cutover runbook (per wave)

<!-- T-minus timeline: freeze, port order, carrier coordination, agent cutover, go/no-go points,
smoke tests, comms. -->

## 7. Rollback plan

<!-- Triggers, decision owner, technical rollback per layer (numbers/carrier, flows, agents,
integrations), time to roll back, and what cannot be rolled back. -->

## 8. RACI

<!-- Table: activities x (onshore architect, onshore PM/BA, Pune devs, Pune QA, Monterrey QA/UAT,
LFG product owner, LFG telephony, ServiceNow team, carrier). -->

## 9. Hypercare, knowledge transfer and decommissioning

<!-- Hypercare length and staffing, KPIs watched, exit criteria, KT plan to LFG run team,
decommission and data retention for legacy recordings. -->

## 10. Risks, assumptions and decisions

<!-- Top risks with mitigation and owner; key decisions as short ADR lines. -->
