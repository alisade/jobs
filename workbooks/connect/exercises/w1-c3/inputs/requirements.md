# LFG Enterprise Help Desk - resiliency requirements (from the CIO staff review, 2026-09-22)

Business context
- The IT service desk is a tier-1 service: during a regional outage employees still need password
  resets, MFA re-enrolment and outage reporting. Trading-floor and branch staff cannot work without it.
- Regulators (state banking examiners) ask for a documented, tested DR plan for "critical customer and
  employee support channels" each year.

Targets
- Voice: RTO 15 minutes for inbound calls to be answered by a human or self-service; RPO for contact
  records and recordings: 15 minutes.
- Chat (employee portal widget): RTO 30 minutes.
- Planned failover drill twice a year without employee-visible disruption beyond 5 minutes.
- Normal operations: us-east-1 primary. us-west-2 is the approved secondary region.

Volumes and staffing
- Peak 1,450 calls/hour (Monday 08:00-10:00 ET), average 650/hour staffed hours; chat 380/hour peak.
- 210 agents: 120 Charlotte (on-site and hybrid), 60 Pune (offshore, follow-the-sun 20:00-06:00 ET),
  30 Monterrey (nearshore). Agents use the custom CCP (Streams) embedded in ServiceNow.
- Major incident (outage reporting) line is 24x7.

Telephony
- Toll-free +1 800 555 0142 (main), +1 800 555 0199 (VIP), 38 DIDs for branches (ported from AT&T in
  2026-08). Two DIDs are with a regional carrier that has not completed the port.
- Avaya stays live in a reduced form until 2027-03 for the trading floor (coexistence, see week 3).

Dependencies
- Lambdas: lfg-identify-caller (Okta + Workday lookup), lfg-password-reset (Okta API),
  lfg-servicenow-incident (ServiceNow Table API). Deployed by the integrations team in us-east-1 only today.
- Lex V2 bot lfg-helpdesk-bot (en_US, es_US). DynamoDB table lfg-caller-cache (on-demand, us-east-1).
- Okta (SaaS, multi-region by vendor), ServiceNow (SaaS, their DR is their problem but its IP allow
  list currently names one NAT gateway in us-east-1).
- Contact Lens (conversational analytics) on all voice; recordings and transcripts to S3 in us-east-1,
  KMS CMK in us-east-1. Data lake export to Athena for the weekly KPI pack.
- Support plan: AWS Enterprise Support.

Constraints
- Budget: the CFO will fund "warm" capacity but asks why the secondary costs anything while idle.
- No DIY multi-region telephony (the security architects want an AWS-supported pattern).
- Change advisory board approves production failover drills; real incidents use the emergency CAB.
