# Reference: connect/w2-c4

Model answer: `.grading/solution/DESIGN.md`. What great looks like:

- Starts from the numbers: the largest lever is demand (34% password/VPN) and AHT (re-identification,
  no screen pop), not the platform rate. Platform cost is well under budget; labor drives B1.
- ServiceNow stays the agent workspace with an embedded CCP, because agents live there; Connect
  agent workspace features (step-by-step guides, views) used where they add value.
- Identity tiers: ANI/portal identification, push verification for privileged self-service, step-up
  for admin and MFA resets. No Voice ID (end of support 2026-05-20); no knowledge questions read back.
- Synchronous Lambda calls in flows stay small (identify, lookup) within the 8 s limit; push polling uses
  async invocation; work notes, summaries and incident updates run on contact events after the contact.
- Routing: dedicated-first, shared-second with delays; proficiency routing for language and SAP/Workday;
  VIP priority; queued callbacks; the staffing estimate: ~30 agents on the phones at the Monday peak
  today (45 scheduled), ~25/37 with screen pop, agent assist and 10% deflection.
- Resiliency: Connect Global Resiliency with a traffic distribution group; dependencies deployed in both
  Regions; DR exercised; alarms on ContactFlowErrors/ThrottledCalls/ConcurrentCallsPercentage.
- Migration: coexistence by number (port in batches; Avaya keeps unported numbers), pilot on new DIDs,
  parallel run per wave, rollback at the carrier before the port is final.
- RACI makes the offshore team responsible for build and the lead accountable for design and reviews.

Common weaknesses: listing features without tying them to requirements; ignoring the 8 s Lambda
budget; proposing SIP trunks between Avaya and Connect without noting Connect has no native BYOC;
no staffing math; no rollback plan; cost model that ignores labor.
