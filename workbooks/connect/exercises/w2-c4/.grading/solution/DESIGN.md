# LFG Help Desk Transformation - Solution Design Document

Author: Lead Amazon Connect architect (Perficient)        Version: 1.0        Status: for design review

## 1. Executive summary

- Replace Avaya (voice/IVR/AACC) and Genesys (chat) with one Amazon Connect Customer instance in
  us-east-1, replicated to us-west-2 with Connect Global Resiliency; keep ServiceNow as the system of
  record and the agent's primary workspace.
- Identify every employee before the agent answers (ANI match for voice, portal SSO context for chat)
  and carry identity, intent and IVR outcome to a ServiceNow screen pop: removes ~40 s re-identification
  and copy-paste per call (pain points 1, 2).
- Self-service first for the 34% of demand that is password reset/unlock and VPN how-to: Lex V2 bot in
  voice and chat with Okta Verify push verification and SSPR, targeting 30% containment (B3).
- One omnichannel routing model (voice + chat) with proficiency-based routing criteria, VIP priority,
  English/Spanish, queued callbacks and a major-incident mode with outbound notifications.
- Generative AI where it pays: agent assist over the ServiceNow knowledge base, after-contact summaries
  into incident work notes, and conversational analytics (formerly Contact Lens) on 100% of contacts.
- Path to production in 4 months: pilot (password reset + VIP) in month 3, waves by queue, Avaya retired
  2027-Q1 after number porting; Genesys chat retired 2027-Q2.
- Outcome model: AHT 438 s -> ~380 s and ~10% demand deflected cut Monday peak staffing from 45 to ~37
  scheduled agents; cost per contact -25% (B1) is reachable mostly through deflection and AHT, not rate.

## 2. Current state and drivers

| Metric | Today | Target |
|---|---|---|
| Voice offered / month | 23,800 | |
| Voice SL | 71% in 30 s | 85% in 30 s |
| Voice abandon | 9.0% | < 5% |
| Voice AHT | 438 s | ~380 s |
| Chat SL | 85% in 60 s | 90% in 60 s |
| FCR proxy | 78% | >= 85% |
| Cost per contact | ~USD 14.20 | -25% |

Drivers the design must fix: no identity hand-off, no screen pop, no self-service for the largest
driver, two siloed channels, manual QA at 0.5%, manual outage notifications, Avaya end of support
(2027-12-31, renewal decision 2027-03-31).

## 3. Requirements traceability and success metrics

| Req | Design element | Measured by |
|---|---|---|
| B1 | Deflection (sec. 9), AHT reduction (sec. 8, 9), vendor-neutral routing (sec. 7) | cost per contact monthly (finance model) |
| B2 | Routing + callbacks (sec. 7), staffing model, forecasting and agent scheduling | Connect historical metrics SL/abandon per queue |
| B3 | Lex self-service, push verification (sec. 6, 9) | containment = self-served / bot sessions, by intent |
| B4 | Screen pop + context, agent assist, summaries (sec. 8, 9) | 7-day repeat proxy from contact records; post-contact survey |
| B5 | Contact-to-incident linkage, contact history in ServiceNow (sec. 8) | % contacts with incident link |
| B6 | Migration waves, porting (sec. 13) | wave exit criteria |
| F1-F2 | Identity tiers (sec. 6) | verification outcome attribute on every contact |
| F3 | Self-service intents (sec. 9) | containment by intent |
| F4 | Queued callback when the queue's oldest contact exceeds 180 s (sec. 7) | callbacks offered/accepted/connected |
| F5 | VIP routing (sec. 7) | VIP SL 95% in 20 s |
| F6 | Major-incident mode (sec. 5) | deflected calls during incidents |
| F7 | ServiceNow integration (sec. 8) | screen pop latency p95 < 2 s |
| F8 | Language routing (sec. 7) | SL per language |
| F9 | Real-time dashboards, conversational analytics, evaluation forms (sec. 10) | % contacts analyzed, QA coverage |
| N1-N2 | Global Resiliency, IaC, DR runbook (sec. 12) | DR test twice a year: RTO <= 15 min |
| N3-N4 | US Regions only, S3 lifecycle, retention (sec. 11) | config audit |
| N5 | Okta SAML, security profiles, CloudTrail (sec. 6, 11) | access review quarterly |
| N6 | Accessible chat widget, TTY/relay (sec. 5) | WCAG 2.2 AA audit |
| N7 | CDK + pipelines (sec. 13) | every change via pipeline |

## 4. Target architecture

```text
 Employees                    AWS us-east-1 (primary)                         LFG systems
 ---------                    -----------------------                         -----------
 PSTN 1-800 / DIDs ---> Amazon Connect Customer instance  <--- ACGR replica (us-west-2)
 Employee portal  ---> chat widget (SSO context JWT)        traffic distribution group
                         |   flows + flow modules
                         |   Lex V2 bot (EN, ES)  --- Lambda: identify, verify, reset ---> Okta API
                         |   Connect assistant (agent assist, ServiceNow KB)            ---> HR directory (Workday)
                         |   routing: queues, profiles, routing criteria
                         |   conversational analytics, evaluation forms
                         v
                Agents: ServiceNow agent workspace + embedded CCP (Okta SAML SSO)
                         |
   contact events (EventBridge) ---> Lambda/Step Functions: screen pop, incident create/update,
                         |                                   after-contact summary -> ServiceNow
   contact records (Kinesis Data Streams) ---> Amazon Data Firehose ---> S3 data lake (Glue/Athena, QuickSight)
   recordings/transcripts ---> S3 (KMS, lifecycle 13 months)
   CloudWatch metrics/flow logs/alarms ---> ops dashboards, PagerDuty
```

| Component | Choice | Why |
|---|---|---|
| Contact center | One Amazon Connect Customer instance, us-east-1 | one routing model, one data model; LFG size does not need multiple instances |
| Resiliency | Connect Global Resiliency replica in us-west-2, traffic distribution group | N1/N2 with a tested failover path |
| IVR / bot | Connect flows + flow modules; Lex V2 with assisted slot resolution and AMAZON.QnAIntent for FAQ | modular flows, NLU for drivers, deterministic DTMF fallback |
| Agent desktop | ServiceNow agent workspace with embedded CCP (Streams) | agents already live in ServiceNow; B5 |
| Agent assist | Connect assistant (AI agents) with ServiceNow knowledge integration | knowledge at the moment of need; AHT |
| Integration | Lambda (TypeScript, Node 22) behind flows; EventBridge contact events for async work | flows stay inside the 8 s synchronous Lambda budget |
| Analytics | Conversational analytics (real-time + post-contact), evaluation forms, contact-record data lake | F9, B4 |
| IaC | CDK (TypeScript) for instance, queues, profiles, hours, flows, Lambda; pipeline per environment | N7 |

## 5. Channels and journeys

| Driver (share) | Channel entry | Self-service | Agent path and context |
|---|---|---|---|
| Password reset / unlock (22%) | voice, chat | identify -> Okta Verify push -> reset link or unlock; 30% containment target | PasswordReset queue; attributes: employeeId, verification tier, failure reason |
| Software / licensing (18%) | chat preferred, voice | ticket status, catalog deep link | GeneralSupport; incident pre-created with driver |
| Laptop / hardware (15%) | voice, portal | warranty/shipment status | GeneralSupport, Spanish via routing criteria |
| VPN / remote access (12%) | voice, chat | how-to via QnAIntent over KB articles | GeneralSupport; bot summary attached |
| SAP / Workday access (10%) | portal, chat | request status | Applications (proficiency SAP/Workday >= 3) |
| MFA enrollment (8%) | voice, chat | guided enrollment link | PasswordReset queue |
| Executives / assistants | VIP DID | none | VIPDesk, priority 1 |

Major-incident mode: a Data Table (or DynamoDB item) holds the active incident flag and message; the
inbound flow module plays it first, offers the status page link by SMS, and routes "this is about the
outage" callers to a short message or the MajorIncident queue. Outbound notifications move from Five9 to
Connect outbound campaigns (SMS and voice) in wave 3.

Accessibility: chat widget themed and tested against WCAG 2.2 AA; voice prompts short, DTMF available on
every menu, TTY users reach agents via relay; no time-limited menus shorter than 5 s.

## 6. Identity, verification and SSO

| Tier | How | Allows |
|---|---|---|
| T0 identified | ANI matches one employee mobile/desk number in the HR directory, or portal JWT (chat) | status, how-to, general routing with screen pop |
| T1 verified | T0 + Okta Verify push approved (Lambda calls Okta Factors API; async polling within the flow using Lambda async mode and a Wait) | password reset/unlock, MFA guidance |
| T2 step-up | T1 + agent-initiated CLEAR verification link (documented Connect integration) or manager callback | admin accounts, MFA reset, VIP sensitive requests |

Voice ID is not used (end of support 2026-05-20). Knowledge questions (SSN last 4, DOB) are retired from
the IVR; HR data is never read back. Agents and admins sign in through Okta with SAML 2.0 (relay state
to the Connect instance); security profiles: Agent, Supervisor (by hierarchy), Admin (break-glass two
named users), with tag-based access control for vendor supervisors to see only their site's queues
and users.

## 7. Routing and workforce design

Queues: PasswordReset, GeneralSupport, Applications, VIPDesk, MajorIncident (24x7), plus chat on the same
queues (one routing model, channel concurrency voice 1 / chat 2).

| Routing profile | Queues (priority / delay) | Agents |
|---|---|---|
| rp-tier1 (Pune, Monterrey) | PasswordReset 1/0, GeneralSupport 1/0, Applications 3/120 | ~130 |
| rp-apps (Charlotte) | Applications 1/0, GeneralSupport 2/45 | ~30 |
| rp-vip (Charlotte) | VIPDesk 1/0, Applications 2/0, GeneralSupport 3/60 | 6 |
| rp-major-incident (on-call) | MajorIncident 1/0 | rota |

Routing criteria (Set routing criteria with predefined attributes): Language=es >= 3 for Spanish callers
(step 1, 60 s), then any; Application=SAP/Workday >= 3 for Applications (step 1, 45 s), then >= 1.
VIP: VIP DID or vip=true from the identity lookup sets queue priority 1. Callbacks: offered when Get queue
metrics shows the oldest contact older than 180 s (a proxy for the predicted wait; queued callback keeps
the place in queue). Hours: one hours-of-operation
per site region plus holiday overrides; the 24x7 line bypasses hours checks.

Staffing (Erlang C, Monday peak 08:30-09:00 ET, 85% in 30 s, max occupancy 85%, shrinkage 32%):

| Scenario | Calls / 30 min | AHT | Agents on phones | Scheduled |
|---|---|---|---|---|
| Today | 99 | 438 s | 30 | 45 |
| Screen pop + agent assist | 99 | 400 s | 28 | 42 |
| + 10% deflection | 89 | 400 s | 25 | 37 |
| Chat peak (concurrency 2, 90% in 60 s) | 41 chats | 696 s | 11 | 17 |

Erlang C ignores abandons and multi-skill effects: routing designs are checked in a routing simulator
before CAB, and production schedules come from Connect forecasting and agent scheduling.

## 8. Integrations

| Integration | Pattern | Notes |
|---|---|---|
| ServiceNow screen pop | CCP embedded in ServiceNow; on contact connected, the agent workspace opens the employee record and the open incidents (Streams contact attributes: employeeId, intent, verification tier, botSummary) | p95 < 2 s; no ServiceNow call on the IVR critical path for screen pop |
| Incident create/lookup | Lambda in flow (lookup open incidents, 2 s budget) and EventBridge contact event handler (create/update after the contact) | OAuth client credentials; idempotency key = ContactId stored in correlation_id; 429 retry with backoff and jitter |
| Work notes and summary | Step Functions on the "contact disconnected" event: fetch analytics output, summarize, redact, write work notes | retries are idempotent; dead-letter to SQS with an alarm |
| Knowledge | Connect assistant knowledge integration with ServiceNow KB; same articles used by QnAIntent | one source of truth for answers |
| Okta | Factors API for push verify; SSPR/unlock via Okta APIs from Lambda (least-privilege API token in Secrets Manager) | async invocation for push polling |
| HR directory | nightly export to DynamoDB (employee, phones, VIP flag, manager) | ANI lookup in < 50 ms |

Failure behavior: every integration degrades to "route to an agent with what we know"; no caller is
dropped because ServiceNow or Okta is slow.

## 9. AI and self-service

- Lex V2 bot (en_US, es_US): ResetPassword, UnlockAccount, VpnHelp, TicketStatus, MfaEnroll,
  TalkToAgent; AMAZON.QnAIntent over the curated KB for how-to questions; assisted slot resolution for
  employee ID and device names; confidence threshold tuned on transcripts from the pilot.
- Agent assist: Connect assistant with an orchestrator AI agent and the ServiceNow knowledge integration;
  custom AI prompt for LFG tone; AI guardrails block HR/PII topics.
- After-contact: summary (issue, actions, resolution, follow-ups) into incident work notes; conversational
  analytics generative post-contact summaries for supervisors.
- Evaluation before go-live: 300-utterance test set per locale (intent accuracy >= 92%), QnA answer
  faithfulness on 100 questions, red-team prompts (injection, abuse); containment and CSAT measured weekly.

## 10. Analytics, quality and reporting

- Conversational analytics on all voice and chat: real-time for supervisor alerts (escalation language,
  negative sentiment trend on VIP), post-contact for categories (driver auto-tagging) and compliance phrases.
- Evaluation forms: one form per channel; automated evaluation for objective items, human calibration
  monthly; QA coverage from 0.5% to 100% automated + 2 human reviews per agent per month.
- Data lake: contact records via Kinesis Data Streams -> Data Firehose -> S3 (Parquet), Glue catalog, Athena;
  QuickSight dashboards for SL, AHT, FCR proxy, containment, driver mix; KPI definitions in one versioned doc.

## 11. Security, privacy and compliance

- Data classes: contact metadata (internal), recordings/transcripts (confidential, may contain PII), HR data
  (restricted, never stored in contact attributes beyond employeeId).
- Redaction: PII redaction in conversational analytics output; downstream consumers read only the redacted
  location; Lambda logs never print attributes.
- Encryption: KMS customer managed keys for recordings, transcripts, data lake; TLS everywhere.
- Retention (N4): S3 lifecycle 13 months for recordings/transcripts, 25 months for contact records,
  ServiceNow keeps incidents 7 years. Legal hold via S3 Object Lock on request.
- Audit: CloudTrail organization trail, Config rules on S3/KMS, Connect configuration only through the
  pipeline; quarterly access review of security profiles.
- Residency: SCPs restrict to us-east-1/us-west-2; no Region outside the US is enabled.

## 12. Resiliency and operations

- Connect Global Resiliency: replica instance in us-west-2, traffic distribution group for telephony
  (100/0), agents distributed via the TDG; flows, queues, profiles replicated; failover runbook rehearsed
  twice a year. Lambdas, DynamoDB (global tables) and secrets deployed to both Regions.
- Monitoring: CloudWatch alarms on ContactFlowErrors, ContactFlowFatalErrors, ThrottledCalls,
  ConcurrentCallsPercentage > 80%, Lambda errors/throttles/duration p95, SL per queue (real-time metrics
  API poller); flow logs retained 30 days.
- Support model: L1 Perficient run team (offshore) with runbooks; L2 Charlotte platform team; AWS
  Enterprise Support case templates. Runbooks: Region failover, Lambda rollback, major-incident mode on/off,
  ServiceNow outage, Okta outage.

## 13. Delivery plan, migration and cutover

| Month | Scope | Exit criteria |
|---|---|---|
| 1 | Foundations: accounts, CDK pipeline (dev/test/prod), instance, SSO, queues/profiles, data lake | pipeline deploys all environments; SSO works for 3 test agents |
| 2 | IVR + bot + ServiceNow integration + agent workspace; routing simulator runs on real demand | UAT scripts pass; load test 2x peak concurrency |
| 3 | Pilot: password reset + VIP on a new DID, 20 agents; conversational analytics on | pilot KPIs >= baseline for 2 weeks |
| 4 | Wave 1 cutover (tier 1 voice) with toll-free port; chat pilot | SL >= 80% for 5 days; rollback rehearsed |
| 5-6 (post-contract or extension) | Waves 2-3: Applications, Spanish, outbound; Genesys exit; Avaya decommission | porting complete; Avaya off |

Cutover: port DIDs in batches after LOA (2-4 weeks per order), keep Avaya routing the remaining numbers
(coexistence by number, not by SIP trunking into Connect), parallel run per wave for 1 week, rollback =
re-point the toll-free number to the Avaya route at the carrier while the port is not final. Test
strategy: flow unit tests in CI (flow lint + simulator), Connect flow tests (test cases via API), IVR
regression calls, load test, UAT with agents from each site, failover test before wave 1.

RACI (R responsible, A accountable, C consulted, I informed):

| Activity | Perficient lead | Offshore team | LFG service owner | LFG ServiceNow/Okta |
|---|---|---|---|---|
| Architecture and design reviews | A/R | C | C | C |
| Flows, Lambda, CDK | A | R | I | C |
| ServiceNow integration | A | R | I | R |
| UAT | C | R | A | C |
| Cutover and porting | R | R | A | I |
| Hypercare (4 weeks) | A | R | C | C |

## 14. Risks, assumptions and decisions

| Risk | Mitigation |
|---|---|
| Vendor VDI (Citrix) audio quality | VDI optimization per Connect docs, endpoint test utility at each site before pilot; fallback to thin client for pilot users |
| Porting delays | start LOA in month 1; pilot on new DIDs; coexistence by number |
| Bot containment below 30% | measure intent accuracy in pilot, tune utterances and QnA content; fall back to callbacks |
| Okta API rate limits during incidents | queue verification requests, cache factor enrollment, circuit breaker to agent path |
| Offshore ramp | design reviews weekly, code review gates in the pipeline, paired builds in month 1 |

Decisions (ADR summary):
1. ServiceNow stays the agent workspace (vs Connect agent workspace): agents live there; Connect step-by-step
   guides used only for VIP and password-reset guidance inside the embedded CCP.
2. One instance + Global Resiliency (vs two independent instances): simpler routing and reporting.
3. CDK for Connect resources (vs Terraform): LFG platform standard; flows deployed as content with ARN
   substitution per environment.
4. Push verification replaces knowledge questions: better security and faster calls.
5. Coexistence by number during migration (vs SIP trunking between Avaya and Connect): avoids unsupported
   BYOC patterns.

## 15. Cost model

Assumptions: current volumes; voice minutes per call ~9.1 (IVR 1.2 + queue 0.6 + handle 7.3);
chat ~30 messages per chat; list prices for Connect Customer (voice USD 0.038/min, chat USD 0.010/message,
AI capabilities included in channel pricing); telephony (DID/toll-free per-minute) per the Connect pricing
page for the US, to be confirmed by LFG procurement.

| Item | Monthly estimate |
|---|---|
| Connect voice usage (23,800 x 9.1 min) | ~USD 8,200 |
| Connect chat usage (9,100 x 30 msgs) | ~USD 2,700 |
| Telephony (toll-free + DID minutes) | ~USD 4,000-6,000 (confirm rates) |
| Lambda, EventBridge, Step Functions, DynamoDB, Firehose, S3, KMS | ~USD 1,500 |
| Bedrock (summaries outside Connect) and Lex | ~USD 1,500 |
| Total platform | ~USD 18,000-20,000 (budget USD 45,000) |

Platform cost is ~USD 0.55 per contact. Labor dominates (today ~USD 13+ of USD 14.20): the 25% target is
met by deflection (~10% of contacts), AHT 438 -> ~400 s and better occupancy, and by retiring Avaya/Genesys
licenses and maintenance.
