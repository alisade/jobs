# LFG CRM / ITSM current state (discovery notes, 2026-09-30)

## Systems
- ServiceNow ITSM (Washington DC release, upgrading to the next family in Q2 2027). IT help desk incidents,
  requests (service catalog), knowledge base (1,850 published KB articles), CMDB. 14,000 employee users.
  Integration user for Connect: none yet. MID servers on premises (Charlotte DC).
- Salesforce Service Cloud (Enterprise Edition, Lightning). Used by HR Shared Services ("People Desk",
  65 agents) for benefits and payroll cases; owned by HR IT. Uses Omni-Channel for email and web cases.
  Currently on Avaya for voice with a screen-pop shim that is end of life in 2027.
- Amazon Connect (target): LFG-owned instance in 111122223333, us-east-1 (DR us-west-2 with Global
  Resiliency). IT help desk wave 1 (220 agents), People Desk wave 3 (65 agents).
- Okta is the workforce IdP for ServiceNow, Salesforce and (planned) Connect via SAML 2.0.

## Volumes (IT help desk, monthly)
- Voice 41,000 contacts, chat 18,500, email (portal) 9,000. 62% create or update a ServiceNow incident.
- People Desk: voice 6,200, web cases 4,100.

## Pain points
- Agents re-key caller details: AHT +45 s per call (time study, Aug 2026).
- 7% of IT calls create a duplicate incident (agent opens a new one instead of finding the caller's open one).
- People Desk agents work in Salesforce all day; switching to a separate softphone window is a top
  complaint in the HR agent survey.
- Audit asked for every voice/chat contact to be traceable to a ticket (incident or HR case) for 7 years.
