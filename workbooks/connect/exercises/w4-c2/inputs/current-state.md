# LFG contact center current state (discovery workbook extract, 2026-09-30)

## Platforms

| Platform | Use | Seats | Contract / support | Notes |
|---|---|---|---|---|
| Avaya Aura CM 8.1 + Experience Portal 8.1 + AACC 7.1 | IT help desk voice (VDN 47100 main, 47120 VIP, 47150 password-reset self-service, 47190 outage line) | 180 agents (3 sites) | Avaya support renewal due 2027-03-31; CM hardware out of warranty | 62 vectors, 31 VDNs, 9 Orchestration Designer apps (password reset, badge lookup) |
| Genesys Engage 8.5 (chat) | Employee portal chat | 40 agents (shared with voice) | Partner support ends 2027-06-30 | 14 routing strategies (IRD), 3 Composer apps; chat transcripts to ServiceNow via custom middleware |
| Five9 VCC | Outbound notifications (outage callbacks, laptop refresh) + Monterrey overflow inbound | 25 agents | Renewal 2027-01-31 | 18 IVR scripts, 6 campaigns, REST integration to ServiceNow |
| Cisco UCCE 12.6 + CVP (Ridgeway Capital, acquired 2025) | Ridgeway IT desk | 30 agents | 12.6 end of support 2027-12-31 | 22 ICM scripts, 7 Call Studio apps |

## Volumes (monthly, Sept 2026)

| Channel | Contacts | AHT | Peak hour | Abandon | Service level (80/60 target) |
|---|---|---|---|---|---|
| Voice (Avaya) | 96,000 | 7m 40s | 1,450 calls Mon 08:00-09:00 ET | 9.8% | 71% |
| Chat (Genesys) | 31,000 | 11m 10s | 420 Mon 09:00 | 4.1% | 83% |
| Outbound (Five9) | 22,000 dials | n/a | campaigns | n/a | n/a |
| Ridgeway voice (Cisco) | 14,000 | 6m 55s | 210 | 6.2% | 78% |

Top call drivers: password reset / MFA reset 31%, access requests 14%, VPN/remote 11%,
laptop/hardware 10%, outage reports 6% (spikes to 40% during incidents), other 28%.

## Telephony

- 312 DIDs + 4 toll-free numbers (Avaya, carrier: Lumen SIP trunks via Avaya SBCE at two data
  centers); 41 DIDs + 1 toll-free on Cisco CUBE (carrier: Verizon). Five9 numbers are Five9-owned.
- Toll-free porting lead time quoted 2-4 weeks; DID port orders 10-15 business days per batch;
  carrier requires a LOA per billing account; ports happen in maintenance windows only.

## Integrations

ServiceNow ITSM (incident create/lookup, CTI screen pop via the Avaya AES + custom adapter),
Okta (agent SSO for Genesys and Five9; Avaya agents use Equinox logins), Active Directory
(password-reset self-service via Experience Portal + a .NET web service), Verint WFM and QM
(recording for Avaya), NICE inContact recordings archive (legacy, read-only).

## Constraints and people

- Quarter-end close blackout: no production changes 2026-12-21 to 2027-01-08 and the last 5
  business days of each quarter.
- Executive sponsor wants Avaya off before the 2027-03-31 renewal.
- Delivery team: Perficient onshore lead architect (you), 1 onshore PM, 1 onshore BA; Pune
  offshore: 8 Connect/Lambda devs, 2 QA automation; Monterrey nearshore: 4 QA/UAT testers
  and the overflow agents. LFG: IT service desk director (product owner), telephony engineer,
  ServiceNow platform team, security (CISO office), workforce management lead.
- Unions/works council: none. Accessibility: Section 508 conformance required for IVR and chat.
