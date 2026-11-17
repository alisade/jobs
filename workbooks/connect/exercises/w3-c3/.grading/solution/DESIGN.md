# DESIGN: LFG hybrid coexistence and number porting cutover plan

Model answer. Capabilities cited are from the Amazon Connect Customer admin guide (telephony,
porting, conversational analytics for external voice systems, Global Resiliency) and the
Chime SDK administrator guide (Voice Connector, PSTN audio maintenance mode and migration).

## 1. Context, goals and non-goals

Goals: move every help desk number to Amazon Connect Customer by wave, keep 1-800-555-0142
up throughout, give security recordings and analytics on all help desk calls from Wave 1,
and let agents on either platform transfer with context.

Non-goals: moving the back-office Avaya users (they stay on Avaya behind the Voice Connector
trunk), migrating Five9 outbound campaigns (separate workstream), replacing the Avaya
reception DID 212-555-4400.

Success: all help desk numbers ported and mapped to Connect flows, ACGR enabled (it requires
ported, not merely forwarded, numbers), no Sev1 caused by a port event, Lumen SIP trunk
cancelled before 2027-03-31.

## 2. Number inventory analysis

| Ticket | Numbers | Carrier / country | Wave | Notes |
|---|---|---|---|---|
| T1 | 1-800-555-0142 | Lumen RespOrg, US toll-free | port after Wave 2 (target 2027-02-09) | critical path; AWS becomes RespOrg; request submitted no earlier than 30 days before |
| T2 | 212-555-0150..0159 | Verizon, US DID | Wave 3 (2027-03-02) | partial range from Verizon's block; VIP desk 0150 |
| T3 | 312-555-0170..0179 | AT&T, US DID | Wave 3 (2027-03-02) | PRI into the Chicago G450; retire the PRI afterwards |
| T4 | 416-555-0190 | Bell Canada, CA DID | Wave 3 (2027-03-02) | Canada is in the 2-4 week US/CA band; bilingual prompts ready before port |
| T5 | +44 20 7946 0123 | BT, GB DID | Wave 4 (2027-05-11) | outside US/CA: 2-6 months, extra documents per the Region requirements page; open the ticket now |
| T6 | 1-888-555-0177 | AWS Chime SDK (SMA) | Wave 3 | not a carrier port: "Phone number port from Chime SDK to Connect" support case, 2-4 weeks; rebuild the hotline as a flow first (PSTN audio in maintenance mode) |
| - | 212-555-4400, 4401..4499 | Verizon | stays | back-office, stays on Avaya; trunk via Voice Connector |
| - | 646-555-0133 | Verizon | decision needed | Five9 caller ID; must be claimed/ported to Connect (or custom caller ID approved) before Connect can present it |

Separate tickets per carrier and country (T1-T5) as AWS requires. Ten distinct ranges or
locations would make this an AWS "project" with SA/TAM involvement; we are at 6 tickets and
engage the account team anyway because of ACGR.

## 3. Coexistence architecture

```text
             PSTN
   +----------+-----------------------------+
   |                                        |
 Lumen TF / Verizon / AT&T / Bell / BT      AWS-managed carriers (Connect)
   |                                        |
 Avaya SBCE (Ashburn A/B, Dallas DR)     Amazon Connect Customer (us-east-1, ACGR us-west-2 later)
   |   \__ Voice Connector trunk (back-office only, PBX <-> PSTN)
 Avaya CM vectors/VDNs -- PSTN forward to Connect-claimed DID bank --> Connect flows
   ^                                                                   |
   +---------- Transfer to phone number (Avaya DIDs still on Avaya) ---+
 Avaya SBCE -- SIPREC fork --> conversational analytics connector (external voice) --> Connect
```

Primary platform per wave:

| Number | Waves 1-2 | After T1 port | Wave 3 | Wave 4 |
|---|---|---|---|---|
| 1-800-555-0142 | Avaya primary; vector routes a growing share to Connect | Connect primary; non-migrated skills forwarded to Avaya DIDs | Connect | Connect |
| VIP/password/Chicago/Toronto | Avaya | Avaya (Connect forwards to them) | ported, Connect | Connect |
| London | Genesys | Genesys | Genesys | ported, Connect |

During Waves 1-2 Avaya stays primary on 1-800 and its vector sends calls for migrated skills
to a bank of Connect-claimed DIDs over the PSTN (AWS documents "forward to Connect numbers
until fully converted, then port" because it keeps a fallback). We do not bridge the Voice
Connector trunk into Connect: AWS does not support that without an architecture review, and
there is no native BYOC trunk into Connect.

Recordings and analytics on Avaya calls (constraint 6): the Avaya SBCE forks a SIPREC copy
of help desk calls to a Connect conversational analytics connector ("external voice
systems"). Each stream must carry `AmznConnectAgentUserId`, so every Avaya help desk agent
gets a Connect user (needed anyway for their wave). Request the connector quota (default 0)
and the recording-sessions quota in month one.

## 4. Context passing between platforms

Connect does not document receiving UUI or X- SIP headers from PSTN callers or sending them on
Transfer to phone number, so context cannot ride the call. Pattern:

- A small "handoff" API (API Gateway + Lambda + DynamoDB with a 10-minute TTL) keyed by a
  transfer DNIS from a pool of 20 Connect-claimed DIDs plus the caller's ANI.
- Avaya -> Connect: the Avaya vector (via Experience Portal or AES) posts {employeeId,
  incident, ANI} to the API, gets a pool DID, and routes to it. The Connect flow on that DID
  reads the record by DNIS + ANI, sets contact attributes and screen-pops ServiceNow.
- Connect -> Avaya: the flow's Lambda writes the record keyed by the Avaya target DID + ANI
  before Transfer to phone number; the Avaya agent desktop looks it up via the same API.
- Fallback when no record matches: the agent sees "unverified" and re-verifies; never block
  the call.

## 5. Porting plan

- Documents: one LOA per ticket signed by the account holder, latest carrier bill, Customer
  Service Record for each range; for GB, the extra documents listed on the Region
  requirements page. A rejected LOA resets the timeline, so the telephony lead checks every
  LOA against the CSR before submission.
- Windows: US/CA requests cannot be submitted more than 30 days before the port date; US/CA
  completes typically 2-4 weeks after portability is verified; outside US/CA 2-6 months.
  Hence: open T5 (UK) now; T1 request on 2027-01-12 for 2027-02-09; T2-T4 requests on
  2027-02-01 for 2027-03-02.
- Freezes: no port dates between 2026-12-18 and 2027-01-04 or in the last five business days
  of a quarter (2027-03-25..31). All dates above avoid them.
- Before each port date: claim a temporary number, map it to the production flow, and run
  the full test matrix on it (AWS recommends testing flows before porting).
- In the ticket: instance ARN, E.164 numbers, the exact flow name to map each number to, the
  port date and a maintenance window outside 06:00-20:00 ET.

## 6. Cutover runbook (T1: 1-800-555-0142)

| When | Action | Owner |
|---|---|---|
| T-30 d | Submit the AWS porting case; Lumen CSR and LOA attached; confirm RespOrg change path | LFG telephony lead |
| T-21 d | Temporary claimed toll-free mapped to `LFG Help Desk Inbound`; Pune NOC runs the 60-call test matrix (menu paths, VIP, after hours, failover) | NOC + QA |
| T-14 d | Go/no-go 1: test matrix green, Wave 2 KPIs stable 2 weeks, agents trained | Program manager |
| T-7 d | Comms: service desk banner, Lumen and AWS confirm the window; last date to reschedule (needs 5 business days) | PM |
| T-1 d | Go/no-go 2; Avaya vectors left intact; forward-back DIDs verified | Telephony lead |
| T-0 22:00 ET | Port executes (RespOrg change). Monitor: test calls every 2 minutes from 3 carriers and 2 mobile networks; CloudWatch CallsPerInterval, ContactFlowErrors | NOC |
| T-0 +15 min | If calls fail on both carriers: invoke rollback level 2 (section 8) | Telephony lead |
| T+1 d | Hypercare: KPIs vs baseline, recordings and analytics flowing, abandon rate | Ops |
| T+7 d | Close; schedule Lumen trunk disconnect after T2-T4 complete | PM |

## 7. Parallel run and validation

- Waves 1-2: parallel run by percentage in the Avaya vector (10% -> 50% -> 100% of migrated
  skills over 3 weeks). Compare per day: service level, abandon rate, AHT, transfer rate,
  repeat contacts within 24 h, and sample recordings from both sides (conversational
  analytics covers both).
- Exit criteria: two consecutive weeks within 5% of Avaya baseline on service level and
  abandon rate, zero Sev1/Sev2 attributable to Connect, all test-matrix paths green.

## 8. Rollback plan

- Before the port: rollback is changing the vector percentage back to 0. Minutes.
- During the window (before RespOrg completion): rescheduling needs 5 business days, and
  once the number moves to the new RespOrg the port cannot be cancelled, so the go/no-go at
  T-1 is the last cheap decision.
- After the port: "rollback" means forward-back, not un-port. Reverting needs a new LOA with
  the losing carrier (a port away). Level 1: the Connect flow sends affected menu paths to
  Avaya DIDs with Transfer to phone number. Level 2: the entry flow forwards all calls to the
  Avaya main help desk DID. Keep Avaya help desk vectors, agents' Avaya logins and the forward
  DIDs live until T+30 days.

## 9. Risks and mitigations

| Risk | Mitigation | Owner |
|---|---|---|
| LOA rejected (name/address mismatch) resets the clock | CSR check before submission; one ticket per carrier | Telephony lead |
| UK port takes 6 months | Open now; Wave 4 date contingent | PM |
| Context lost on cross-platform transfers | Handoff API with TTL, unverified fallback | Integration lead |
| Concurrent call quota (default 10) | Raise concurrent calls and phone number quotas before Wave 1 | AWS account team |
| ACGR not possible until ports complete | Plan ACGR enablement after T1-T4 | Architect |
| Hotline (Chime SDK) closed to new features | Rebuild as flow in Wave 3, then Chime-to-Connect port case | Architect |
| Outbound caller ID for Five9 number | Decide: port 646 number to Connect with outbound migration, or leave on Verizon | Product owner |

## 10. RACI and communications

| Activity | LFG telephony | Pune NOC | Monterrey | Carriers | AWS | Service desk |
|---|---|---|---|---|---|---|
| Port tickets and LOAs | A/R | I | I | C | R | I |
| Test matrix on temp numbers | A | R | R | - | C | I |
| Cutover window monitoring | A | R | I | C | C | I |
| Rollback decision | A/R | C | I | C | C | I |
| User comms | C | I | I | - | - | A/R |

Daily stand-up during port weeks at 08:30 IST / 22:00 ET overlap; runbook in Confluence with
NOC sign-off per step.

## 11. Open questions and decisions needed

1. Five9 outbound caller ID number: port with the outbound migration or leave?
2. Does security accept SIPREC analytics for Avaya calls as closing AF-2026-14 before Wave 3?
3. AWS confirmation of quotas: concurrent calls, analytics connectors, recording sessions.
4. Avaya CM renewal: can Avaya be reduced to back-office licences after Wave 3?
