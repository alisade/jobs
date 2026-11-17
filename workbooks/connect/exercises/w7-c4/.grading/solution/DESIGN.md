# Design: CRM/ITSM integration for LFG on Amazon Connect (ServiceNow + Salesforce)

## Context and requirements

LFG is moving IT help desk (wave 1, 220 agents) and HR People Desk (wave 3, 65 agents) onto one
LFG-owned Amazon Connect instance. IT works incidents in ServiceNow ITSM; People Desk works HR cases in
Salesforce Service Cloud Lightning. The decision drivers:

- R6 (LFG owns telephony, flows, data and the AWS bill) and R7 (one instance, shared front door and WFM)
  rule out any option where a vendor provisions the Connect instance in its own AWS account.
- R3 (agents stay in their system) means two different agent desktops on one instance.
- R2/R4 (exactly one ticket per contact, contact logged on the ticket for 7 years) need an idempotent
  write path that does not depend on the agent remembering to click.
- R10 (2 onshore + 4 offshore after hypercare) favors vendor-supported packages over bespoke UI.

## Options considered

ServiceNow (IT help desk):

| Option | Instance owner | Gives you | Fit |
|---|---|---|---|
| A1 Custom: Connect agent workspace + LFG workspace app, Lambda/Table API integration | LFG | full control; screen pop from flow attributes and Customer Profiles; incident write via API | R1 R2 R4 R6 R7 strong; more code to own |
| A2 ServiceNow-built "ServiceNow Voice with Amazon Connect" (CTI in the ServiceNow agent workspace) | LFG (customer's Connect instance) | softphone inside ServiceNow, interaction records | R3 for ServiceNow-centric agents; ServiceNow licensing; not AWS-documented (vendor-supported) |
| A3 Customer Profiles AppFlow integration for ServiceNow (standard profile + case mapping) | LFG | ServiceNow cases/users ingested into profiles for screen pop | complements A1 for R1; read-only, batch/near-real-time, not a ticket writer |

AWS documents A3 and the agent assist ServiceNow knowledge connector; AWS does not document its own
ServiceNow CTI adapter, so A2 is a ServiceNow product decision with ServiceNow support.

Salesforce (People Desk):

| Option | Instance owner | Gives you | Fit |
|---|---|---|---|
| B1 Amazon Connect CTI Adapter for Salesforce (AppExchange managed package + serverless app in LFG's account) | LFG | CCP embedded in Lightning, screen pops, click-to-dial, CTI Flows, activity/call logging | R3 R5 R6 R7 strong; AWS-maintained open-source project |
| B2 Service Cloud Voice, bundle | Salesforce (Salesforce-managed AWS account, billed by Salesforce) | native Voice Call records, Omni-Channel, real-time transcript in console | violates R6 and R7 (second instance, data in a Salesforce-managed account) |
| B3 Service Cloud Voice with partner telephony from Amazon Connect ("bring your own Amazon Connect") | LFG | native SCV console experience on LFG's instance, SSO from Salesforce | R3 R6 R7 strong; SCV licensing; heavier setup and version coupling |

Scoring (0-2 per requirement, R1-R10): A1 17, A2 14, B1 17, B2 9, B3 17. B1 and B3 tie on fit; the
tiebreaker is People Desk's wish for Omni-Channel unified routing of web cases and calls (B3) versus cost
and simplicity (B1). Recommendation: B1 now, revisit B3 when HR renews Salesforce licensing in 2027
(open question Q2).

## Recommended architecture

```
 PSTN / chat widget / portal
          |
   Amazon Connect (LFG, us-east-1, ACGR replica us-west-2)
   shared front door flow -> Lex bot -> route by LOB (IT | HR)
      |                                   |
  IT queues                          HR queues (People Desk routing profile)
      |                                   |
 Connect agent workspace             Salesforce Lightning + CTI Adapter (embedded CCP)
  + LFG help desk app (3P app)        screen pop: contact attrs -> SF case/contact search
  + ServiceNow in browser             click-to-dial, call logging (CTI Flows)
      |                                   |
      +---- EventBridge: Amazon Connect Contact Event (DISCONNECTED, CONTACT_DATA_UPDATED)
                 |
          Step Functions "log-contact" (idempotent on ContactId)
           |-> ServiceNow Table API: incident work note + interaction link (IT)
           |-> Salesforce REST: Task/Voice log on the HR case (HR, if CTI Adapter did not log it)
           |-> DynamoDB contact-ticket ledger (ContactId PK, conditional put) -> 7-year retention
```

IT call: IVR identifies the caller (Customer Profiles `_phone` search, verification state), the Lambda
looks up open incidents and creates one with `correlation_id = ContactId` if needed (w7-c1), the flow sets
handoff attributes, the agent app shows them (w7-c2). After disconnect the EventBridge-driven step adds the
recording link and Contact Lens summary to the incident work notes.

HR call: front door detects HR intent, People Desk queue, CTI Adapter pops the Salesforce contact (search by
employee number attribute, not phone) and the open case; CTI Flows log the call activity on the case.

## Screen pop and context passing

Source of truth for context is contact attributes set by the flow (bot summary, intent, verification,
incident/case number) because both desktops can read them: the agent workspace app via the Amazon Connect
SDK, the CTI Adapter via Streams contact data. Lookups happen in the IVR Lambda inside a 3-6 s budget; if
ServiceNow is slow the flow continues with `status=DEGRADED` and the app does the lookup on answer.

## Contact and ticket logging

- Idempotency key: ContactId (InitialContactId for transfers and persistent chat). A DynamoDB ledger
  entry is written with `attribute_not_exists(contactId)` before creating anything; ServiceNow
  `correlation_id` and a Salesforce external id field hold the same key so retries and replays never
  duplicate (R2).
- Logging is event-driven (EventBridge contact events + contact records) rather than relying on the agent,
  with retries and a DLQ; a nightly reconciliation compares contact records to the ledger (R4, audit).
- Recordings and transcripts stay in LFG's S3 with retention per class; tickets hold links, not media (R6, R9).

## Identity, access and security

Okta SAML for Connect (relay state to the instance), ServiceNow and Salesforce (R8). One instance, two
LOBs: security profiles with tag-based access control on queues, routing profiles and users (`LOB=IT|HR`),
separate agent hierarchies for reporting. HR contacts never put case details in contact attributes; only
the Salesforce case id travels (R9). Integration users: ServiceNow least-privilege role scoped to
incident/sys_user; Salesforce integration user with a permission set limited to Case/Task; secrets in
Secrets Manager with rotation.

## Operations, ownership and cost

After hypercare the 6-person team owns flows (IaC, promotion pipeline), the help desk app, the logging
Step Functions and the CTI Adapter upgrades (managed package + serverless app versions, pinned and tested in
a Salesforce sandbox before prod). ServiceNow family upgrades are regression-tested against the Table API
contract. Cost: Connect per-channel usage billed to LFG; the CTI Adapter itself is a free AppExchange package plus a serverless app in LFG's account; B3
would add Service Cloud Voice licensing per HR agent.

## Risks and open questions

- Risk: CTI Adapter and SCV evolve on Salesforce's release train; mitigate with sandbox regression per
  release and a pinned adapter version.
- Risk: one instance for two LOBs raises blast radius of a bad flow release; mitigate with per-LOB flows,
  modules with versions/aliases, flow test cases in CI, and staged promotion.
- Q1: does Audit accept ticket links (not copies) for the 7-year traceability?
- Q2: will HR fund Service Cloud Voice partner telephony in 2027 for Omni-Channel unification?
- Q3: ServiceNow Voice (A2) for a future ServiceNow-centric team: who supports it, ServiceNow or LFG?

## Decision record

Decision: IT on the Connect agent workspace with an LFG workspace app and a custom ServiceNow integration
(A1 + A3 for profiles); People Desk on the Amazon Connect CTI Adapter for Salesforce (B1); one LFG-owned
instance; event-driven, idempotent contact-to-ticket logging. Status: proposed. Consequences: LFG owns more
integration code (mitigated by tests and the promotion pipeline); Service Cloud Voice bundle is rejected
because it puts the instance and contact data in a Salesforce-managed account; B3 stays open for 2027.
