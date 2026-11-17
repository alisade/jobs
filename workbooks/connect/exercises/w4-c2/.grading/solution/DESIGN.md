# LFG help desk migration program plan (Avaya / Genesys / Five9 / Cisco -> Amazon Connect)

## 1. Goals, scope and success criteria

In scope: IT help desk voice (Avaya, 180 seats), employee chat (Genesys), outbound notifications
and Monterrey overflow (Five9), Ridgeway desk (Cisco UCCE/CVP); ServiceNow, Okta, AD self-service,
recording/QA. Out of scope: Verint WFM replacement (decision in wave 4), NICE archive (retain
read-only, see 9).

| Criterion | Target |
|---|---|
| Service level 80/60 voice | >= 80% by end of hypercare (today 71%) |
| Abandon voice | <= 6% (today 9.8%) |
| Password/MFA reset containment | >= 45% of reset calls self-served |
| Avaya CM decommissioned | before 2027-03-31 renewal |
| Five9 off | before 2027-01-31 renewal, or 3-month extension signed by 2026-11-15 |
| Cisco off | before 2027-12-31 end of support |
| Zero P1 incidents caused by cutover | each wave |

Hard dates: blackout 2026-12-21 to 2027-01-08 and last 5 business days of each quarter.

## 2. Migration strategy and waves

| Wave | Moves | Why this order | Dates | Exit criteria |
|---|---|---|---|---|
| 0 Foundation | Connect instances (us-east-1 + ACGR replica us-west-2), IaC pipeline, Okta SAML, ServiceNow integration, recording/Contact Lens, agent desktop | Everything else depends on it | Oct 12 - Nov 6 | security sign-off, pipeline promotes dev->test->prod, test number end to end |
| 1 Pilot | Outage line VDN 47190 + 2 toll-free + 20 agents; Five9 outbound outage callbacks -> Connect outbound campaigns | Low volume, simple flows, proves porting and outbound | Nov 9 - Nov 27 | 2 weeks stable, SL >= target, no P1 |
| 2 Main help desk | VDN 47100, 47120 VIP, 47150 reset self-service (Lex + Lambda to AD), 180 Avaya agents in 3 cohorts | 80% of volume; before the Avaya renewal | port Mon Jan 11 2027 after blackout; agents cohort by site over 2 weeks | parallel run green, SL, containment trend |
| 3 Chat + Five9 overflow | Genesys chat -> Connect chat with Lex handoff; Monterrey overflow inbound | Genesys support to 2027-06-30; Five9 renewal | Feb 1 - Feb 26 2027 | chat SL, transcripts in ServiceNow |
| 4 Ridgeway (Cisco) | 41 DIDs + 1 toll-free from CUBE/Verizon, 22 ICM scripts | Separate carrier and team; EOS end 2027 | Apr - May 2027 | same gates |
| 5 Decommission | Avaya CM/AAEP/AACC, Five9, Genesys, Cisco | contracts | Mar - Jun 2027 | data retention done |

Five9: wave 1 + 3 do not fit before 2027-01-31 for overflow inbound, so negotiate a 3-month
month-to-month extension for the overflow campaign only (decision D3).

## 3. Coexistence during migration

AWS Prescriptive Guidance for Avaya lists three options; we use option 3 ("ingress to Connect,
egress to Avaya") per number block once a wave's numbers are ported, and keep Avaya as the
ingress for unported numbers. Cross-platform transfers: Connect transfer to phone number into an
Avaya VDN for skills not yet migrated (a short list in wave 2), Avaya route-to number into a
Connect DID for migrated ones. Context across the gap: pass a ServiceNow incident number in a
DTMF-free way by creating/looking up the incident before transfer (keyed by ANI + time) because
UUI/X- header pass-through into Connect is not a documented capability. Screen pops: Connect
agents use the new desktop (ServiceNow via Lambda); Avaya agents keep AES pops until their cohort
moves. Agents are never on both platforms in the same shift.

## 4. Build approach (migration factory)

1. Inventory every vector/VDN, ICM script, Five9 script and IRD strategy with volume per entry
   point (CMS/ICM reports). 62 vectors -> rationalise: 19 have < 50 calls/month and are merged
   or retired with the product owner.
2. Target patterns first (modules: closed/holiday, identify caller, menu, queue with staffing
   check), then translate with the lfg-legacy-translator; humans review every flow.
3. Each script gets a golden call-path suite (times, holidays, staffing, key presses) run legacy
   vs Connect in CI; definition of done = lint clean + suite green + PO sign-off + prompts approved.
4. Prompts: re-record the top 30 announcements, TTS (neural voice) for the rest.

## 5. Validation and testing

| Test | Owner | Gate |
|---|---|---|
| Path-suite validation legacy vs Connect, incl. DST and holiday dates, config lint (hours zones) | Pune QA | 100% green |
| Integration tests (ServiceNow, AD reset, Okta) | Pune devs | green in test |
| Native flow tests (Connect test cases in CI) + synthetic calls every 15 min | Pune QA | green |
| UAT scripts by call driver | Monterrey QA + LFG PO | signed |
| Load test 1.5x peak hour (2,200 calls/h) with a partner load tool; Lambda/ServiceNow p99 | Architect | p99 < 1 s, no throttles |
| Accessibility (Section 508): IVR timing, chat widget WCAG | BA | pass |
| Parallel run: test DIDs on Connect for 1 week, real agents | PO | KPIs within 5% |

## 6. Cutover runbook (per wave)

- T-15 bd: port order + LOA submitted (toll-free T-20 bd); freeze vectors for the moving VDNs.
- T-5: go/no-go 1 (suite green, UAT signed, agents trained, rollback rehearsed).
- T-1: agents provisioned and logged in to Connect for a dry run; comms to employees.
- T-0 05:00 ET: carrier activates port; telephony engineer and carrier on bridge; synthetic and
  manual test calls per number; 06:00 desk opens; architect monitors real-time metrics, flow
  errors and Lambda errors; go/no-go 2 at 08:30 after peak start.
- T+1 to T+10: hypercare (see 9).

## 7. Rollback plan

Triggers: P1 caused by Connect, SL < 60% for 2 consecutive hours, flow error rate > 1%.
Decision: LFG service desk director with the architect, within 30 minutes of trigger.
- Before port completion: cancel/stop the port with the carrier.
- After port (numbers cannot be ported back quickly): point the Connect flow for those numbers at
  a "rollback" flow that transfers to the Avaya VDN via a DID still on Avaya (pre-built and tested
  in wave 0), agents log back into Avaya (licenses kept until wave exit).
- Flows: re-publish the previous version; modules: switch alias back.
- Integrations: feature flags in Lambda config.
Not reversible: the port itself (re-port takes weeks), so the rollback path is "Connect as
ingress, Avaya as egress" until the issue is fixed.

## 8. RACI

| Activity | Arch (onshore) | PM/BA | Pune devs | Pune QA | Monterrey QA | LFG PO | LFG telephony | SNOW team | Carrier |
|---|---|---|---|---|---|---|---|---|---|
| Target architecture, patterns | A/R | C | C | I | I | C | C | C | - |
| Flow/Lambda build | A | I | R | C | I | I | - | C | - |
| Path suites, automation | A | I | C | R | C | I | - | - | - |
| UAT | C | R | I | C | R | A | I | C | - |
| Number porting | C | R | - | - | - | A | R | - | R |
| Cutover go/no-go | R | R | C | C | C | A | C | C | I |
| Hypercare | A/R | R | R | R | C | C | C | C | I |

Offshore cadence: daily 30-minute overlap stand-up at 08:30 ET / 18:00 IST, design reviews
twice a week, PR review by the architect for every flow pattern and Lambda; ADRs in the repo.

## 9. Hypercare, knowledge transfer and decommissioning

Hypercare 10 business days per wave (wave 2: 15), war room with Pune evening coverage, daily
KPI review (SL, abandon, AHT, containment, flow/Lambda errors, ServiceNow failures). Exit:
5 consecutive days within targets. KT: runbooks, architecture docs, 6 recorded sessions and
shadowing for the LFG run team; they own wave 4 changes with us reviewing. Legacy recordings:
export Avaya/Verint and NICE recordings needed under the 7-year retention policy to S3 (Object
Lock, Glacier) before decommission.

## 10. Risks, assumptions and decisions

| Risk | Mitigation | Owner |
|---|---|---|
| Port slips past Avaya renewal | file wave 2 ports early Dec; negotiate 1-quarter Avaya extension as fallback | PM |
| Holiday/hours config errors | config lint + DST/holiday dates in path suites | Pune QA |
| AD reset self-service security | step-up verification (OTP via End User Messaging SMS), fraud review | Security |
| Agent adoption | cohort cutover, floor walkers, desktop training | PO |

Decisions: D1 ACGR from wave 0; D2 coexistence option 3 per number block; D3 Five9 overflow
extension; D4 rationalise 19 low-volume vectors; D5 Verint WFM kept until a separate decision.
