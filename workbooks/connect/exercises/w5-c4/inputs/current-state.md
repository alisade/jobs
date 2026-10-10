# LFG help desk - current state and pilot results (input for the design)

Source: LFG service desk reporting, ServiceNow, Connect pilot (2026-08-01 to 2026-09-15).

## Volumes (monthly, after the Avaya/Genesys cutover forecast)

| Channel | Contacts / month | AHT (agent) | Notes |
|---|---|---|---|
| Voice (+1 800 555 0142, internal 4357) | 62,000 | 7.4 min | peaks Mon 08:00-10:00 ET, quarter-end +35% |
| Portal chat | 38,000 | 11.0 min (2 concurrent chats per agent) | grew 40% YoY |
| Email to servicedesk@ | 9,000 | handled in ServiceNow, out of scope | |

Call drivers (voice + chat, from ServiceNow categories and pilot transcripts):

| Driver | Share | Self-service today |
|---|---|---|
| Password reset (AD, SAP, Workday, VPN) | 31% | portal reset exists; IVR reset pilot 9% containment |
| Account unlock | 9% | none |
| How-to / known issue (2,400 ServiceNow KB articles) | 22% | portal search only |
| Access request (new app, share, license) | 11% | ServiceNow catalog item, users call anyway |
| Ticket status | 8% | none |
| Outage report | 5% | none (major incident line) |
| Other | 14% | none |

## Pilot (Lex V2 bot + DTMF fallback in Connect)

- Containment 9% (reset only). 100% of transfers arrived without context; analysts re-asked ID and issue
  (+70 s AHT on transferred calls).
- CSAT for bot-handled contacts 3.1/5; "it kept asking me the same thing" top verbatim.
- Agent desk: 85 FTE (20 onshore Charlotte, 40 Pune offshore, 25 Monterrey nearshore), 24x5 plus weekend on-call.
- Fully loaded analyst cost (blended): USD 0.85 per handled minute.
