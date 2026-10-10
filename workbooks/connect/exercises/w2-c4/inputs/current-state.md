# LFG IT Service Desk - current state (discovery pack, 2026-10)

Prepared by the LFG service owner for the Perficient discovery. Figures are monthly averages for
2026-04..2026-09 unless noted.

## Organization

- Larkspur Financial Group: ~14,000 employees (US 11,200; Mexico 1,400; India 1,400 incl. contractors).
- IT Service Desk: 182 agents (FTE 163) in three sites:
  - Charlotte, NC (LFG employees): 38 agents, tier 2 and Applications (SAP, Workday, Salesforce), VIP desk (6).
  - Pune, India (vendor: Kestrel Services, 6 PM - 4 AM IST shift for US hours): 92 agents, tier 1.
  - Monterrey, Mexico (vendor: Norte BPO): 52 agents, tier 1/general, English and Spanish.
- Hours: 06:00-20:00 ET Mon-Fri; Sat 08:00-14:00 ET; 24x7 major-incident line (on-call).

## Platforms

| Function | Today | Notes |
|---|---|---|
| Voice ACD + IVR | Avaya Aura CM 8.1, Experience Portal 8.0 (Orchestration Designer apps), AACC for agent desktop | hardware support ends 2027-12-31; renewal decision needed by 2027-03-31 |
| Chat | Genesys Cloud CX web messaging, 40 named seats | contract renews 2027-06-30 |
| Outbound notifications | Five9 (outage voice blasts and SMS) | 4 campaigns, used ~6 times/month |
| ITSM | ServiceNow (Washington DC release), Incident, Request, Knowledge (1,900 articles) | agents work in ServiceNow; screen pop via Avaya AACC is manual copy-paste of caller ID |
| Identity | Okta Workforce (SSO, MFA, SSPR), Entra ID for M365 | SSPR adoption 38% of employees |
| Recording / QA | Avaya Workforce Optimization (recording only); QA in spreadsheets, 2 calls/agent/month | |
| Telephony | 2 x SIP trunks (Lumen) to Avaya SBCE in Charlotte; 1-800 toll-free + 46 DIDs; Mexico local DID | porting LOA not started |
| Network | Pune and Monterrey on vendor networks via site-to-site VPN; Citrix VDI for vendor agents | |

## Demand (monthly)

| Channel | Offered | Handled | Abandoned | AHT | Service level | Notes |
|---|---|---|---|---|---|---|
| Voice | 23,800 | 21,650 | 9.0% | 7.3 min | 71% in 30 s (target 80/30) | peaks Mon 08:00-11:00 ET |
| Chat | 9,100 | 8,700 | 4.4% | 11.6 min | 85% in 60 s | concurrency 2 |
| Portal tickets | 6,200 | - | - | - | - | ServiceNow self-service form |

Top call drivers (voice + chat, share of contacts): password reset / account unlock 22%, software
install and licensing 18%, laptop and hardware 15%, VPN and remote access 12%, SAP/Workday access
10%, MFA enrollment 8%, other 15%.

Monday peak half hour (08:30-09:00 ET): ~99 voice calls and ~41 chats.

KPIs: FCR (7-day repeat proxy) 78%; CSAT 3.9/5 (post-ticket survey, 11% response); occupancy 74%;
shrinkage 32%; cost per contact (fully loaded, incl. vendor) ~USD 14.20.

## Known pain points

1. Agents re-ask identity questions after the IVR; the IVR collects an employee ID but cannot pass it.
2. No screen pop: agents search ServiceNow by name; 40 s added per call (time study).
3. Password-reset calls that SSPR could have handled; IVR has no self-service.
4. Chat and voice are separate queues and separate reports; no single view of a contact.
5. Vendor sites depend on Citrix; audio quality complaints from Pune twice a month.
6. Major incidents: outage notifications are manual in Five9; callers flood the line anyway.
7. QA is manual and covers 0.5% of contacts; no sentiment or compliance monitoring.
