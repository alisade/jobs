# Design: AI-assisted help desk self-service and agent assist (LFG)

Model answer. Numbers come from `inputs/`; prices are the illustrative ones in `inputs/prices.md`
and must be re-checked on the AWS pricing pages before they go to a client.

## 1. Goals and success metrics

Baseline (pilot): containment 9% (reset only), 100% of transfers without context, +70 s AHT on
transferred calls, bot CSAT 3.1/5.

| Metric | Phase 1 (wk 8) | Phase 2 (wk 12) | Phase 3 (wk 16) |
|---|---|---|---|
| Voice containment (contained / all voice) | 15% | 25% | 30% |
| Chat containment | 20% | 35% | 40% |
| Transfers with context (summary + intent + verified ID in workspace) | 95% | 98% | 98% |
| AHT on transferred voice | -45 s | -60 s | -70 s |
| Bot CSAT | 3.6 | 3.9 | 4.0 |
| Ungrounded or unentitled answer rate (eval + sampled prod) | 0 on red team, < 0.5% sampled | same | same |

Containment only counts when the contact does not come back on any channel within 24 h for the
same driver (ServiceNow repeat-contact join), so the bot cannot "win" by hanging up.

## 2. Use cases and channel scope

| Driver (share) | Voice | Chat | Why |
|---|---|---|---|
| Password reset (31%) | self-service: verify (ANI + employee ID + OTP), Lex code hook calls reset API | same, Okta-authenticated in portal so no OTP | deterministic API, highest volume |
| Account unlock (9%) | self-service, disabled accounts to Access team | same | deterministic, security exceptions routed |
| How-to / known issue (22%) | RAG answer, short, offer SMS/portal link to article | RAG answer with article links | 2,400 KB articles; biggest AI win |
| Ticket status (8%) | self-service via ServiceNow lookup | same | read-only API |
| Access request (11%) | capture intent + system, create catalog request or hand off | same | approvals stay in ServiceNow |
| Outage report (5%) | detect, check known major incident, route MajorIncident priority 1 | same | humans own incidents |
| Other (14%) | AI agent triage then handoff with summary | same | agent assist carries the value |

Agent assist applies to every handed-off contact.

## 3. Architecture

```text
Caller/Employee
  | PSTN (toll-free, internal 4357)            | Portal chat widget (Okta session, JWT)
  v                                            v
Amazon Connect Customer (us-east-1; ACGR replica us-west-2)
  Inbound flow: identify (Lambda, 3 s) -> verify tier -> Get customer input (Lex V2 LfgHelpDeskBot, alias prod)
     |  Lex code hook Lambda (validation, reset/unlock/status via LFG integration API)
     |  How-to intents -> RAG Lambda (sync, 6.5 s budget) or Lex AMAZON.QnAIntent with bkb-retrieval-filter
     v
  RAG Lambda: entitlements (contact attrs) -> Bedrock Retrieve (KB, metadata filter) -> Converse (Haiku-class,
              us. geographic inference profile) with Guardrail gr-lfg-helpdesk (grounding, PII, prompt attack)
  Handoff: Set contact attributes (summary, intent, slots, verified, articleIds) -> Set working queue -> Transfer
     v
Agent workspace (Okta SAML): step-by-step guide view + screen pop (ServiceNow incident), AI agents
  (formerly Amazon Q in Connect) for real-time recommendations and knowledge search over the ServiceNow KB
  integration; generative post-contact summary for ACW
     v
ServiceNow (system of record): incident/request created by Lambda (OAuth client credentials, idempotent on
  ContactId), work notes from the summary; KB source for both the Bedrock KB and the AI agents integration
Data: Contact Lens (conversational analytics) with redaction, CTR stream -> Firehose -> S3 (13-month lifecycle)
```

Managed features: Connect flows, Lex V2, Bedrock KB/Guardrails/Converse, AI agents, Contact Lens.
Our code: three Lambdas (identify, Lex code hook, RAG), the ServiceNow adapter, the KB exporter
(only if we keep a customer-managed KB), flows and infrastructure as code. Everything in US regions;
the inference profile is the US geographic one (constraint 4 rules out global profiles).

## 4. Conversation design and bot-to-agent handoff

Identity tiers: T0 unverified (generic how-to from public-help articles only); T1 ANI match + employee
ID (status lookups, generic how-to); T2 T1 + OTP to the enrolled MFA device (resets, unlocks, restricted
content). Portal chat is T2 from the Okta session (signed JWT passed as a contact attribute reference,
validated by Lambda, never trusted from the browser as plain text).

Voice: one open question ("Tell me briefly what you need") with Lex, DTMF menu as fallback on every
prompt (accessibility), max two re-prompts then handoff. Chat: same bot, text locale, quick replies.

Handoff contract (Lex session attributes -> contact attributes): `handoff`, `handoffReason`,
`handoffQueue`, `intent`, `slots` (JSON), `summary` (one line for the analyst), `verifiedTier`,
`employeeId`, `articleIds`, `snIncident`. The flow copies them with Set contact attributes (Lex values
are not kept on the contact otherwise), the workspace view renders them, and the ServiceNow Lambda puts
the summary in the incident work notes. Queue priority raised for repeat callers within 24 h.

## 5. Knowledge and retrieval

Source of truth: ServiceNow kb_knowledge. Decision: Bedrock Managed Knowledge Base with the native
ServiceNow connector (GA 2026-09) and its "Crawl ACLs" option, so ServiceNow user criteria drive
entitlements instead of hand-maintained metadata; fall back to a customer-managed KB with an S3
exporter and `.metadata.json` sidecars (department, audience, region, status) if the spike shows a gap.
Note: RetrieveAndGenerate is not available on managed KBs, which fits our Retrieve + Converse design.

Filtering: built only from authenticated attributes; restricted (HR/Legal/Finance) require a matching
department; contractors get all-workers/contractors only; status = published (retired articles kept
for audit but filtered). Chunking: semantic for long troubleshooting articles; hierarchical if answers
need the parent context. Freshness: hourly sync; alarm when ingestion failures > 0 for articles (not
attachments) or when the filtered=0 rate per department moves.

## 6. Safety, privacy and compliance

Guardrail `gr-lfg-helpdesk`: contextual grounding (grounding 0.75, relevance 0.5) with sources passed
as `grounding_source`; prompt attack filter HIGH on input; sensitive information: ANONYMIZE names/emails
in outputs, BLOCK card numbers and SSNs on input; denied topics: HR case advice, legal advice,
"bypass MFA". Caller speech and documents are untrusted: instructions inside sources are data; tools
that change state (reset, unlock, create request) are called by our code after server-side
authorization, never chosen by the model. Model invocation logging to an encrypted, access-restricted
S3 bucket (it contains plaintext, including blocked text), 90-day retention; transcripts and recordings
13 months via S3 lifecycle; Contact Lens redaction on, analysts see redacted transcripts. No card data
is ever spoken to the bot (resets do not need it). Residency: us-east-1/us-west-2 only.

## 7. Agent assist and agent workspace

AI agents (formerly Amazon Q in Connect) with the ServiceNow knowledge integration for real-time
recommendations and manual search during the contact; custom AI prompt tuned to LFG terminology and
evaluated like the bot. Workspace: step-by-step guide view per driver (verified ID, summary, suggested
article, "create incident" with prefilled fields), ServiceNow screen pop by incident sys_id. After
contact: Contact Lens generative post-contact summary pasted to work notes, analyst edits before save.
Supervisors: real-time dashboards by queue, Contact Lens rules for negative sentiment on VIP callers.

## 8. ServiceNow integration

Table API via an integration Lambda: OAuth client credentials (token cached until expiry minus 60 s),
`sysparm_query` lookups (caller sys_user by employee_number, open incidents), create incident with a
correlation id = ContactId and a check-before-create, retries only on 429/5xx with Retry-After and a
total budget; work notes PATCH after the contact. Credentials in Secrets Manager, rotated; Lambda in
a VPC only if ServiceNow is IP-restricted (then NAT, and accept cold-start cost).

## 9. Latency budget

Voice RAG turn (synchronous Lambda, Connect limit 8 s): Lex ASR end-of-speech ~0.6 s, Lambda warm
start ~50 ms (provisioned concurrency during business hours), Retrieve p95 0.6 s (cap 2 s), Converse
Haiku-class p95 2.0 s for <= 300 tokens with the guardrail (~0.2-0.3 s), margin 1 s -> budget 6.5 s,
p95 target ~3 s. Holding audio ("let me look that up") played before the invoke. If the answer path
p95 exceeds 4 s in load tests: Connect async Lambda mode (up to 60 s, Wait + Load Lambda result) with
the holding prompt, or send the answer by SMS/portal link. SDK maxAttempts 2; every failure is a
handoff with reason, never dead air.

## 10. Evaluation plan

Offline: 600 labeled utterances from pilot transcripts (intent), 300 how-to questions with gold
articles (retrieval hit@k, MRR), answer faithfulness and citation precision with Bedrock RAG evaluation
(LLM-as-judge) on 150 questions, plus 100 entitlement probes (restricted content per caller class) and
80 prompt-injection/red-team cases (caller speech and planted documents). Lex Test Workbench and Bot
Analyzer for NLU. Gates for promotion: intent accuracy >= 0.9, hit@3 >= 0.85, faithfulness >= 0.9,
0 entitlement leaks, 0 red-team actions. Pre-prod: 2 weeks shadow mode on 10% of chat (answer
generated, not shown; analysts rate). Online: percentage split in the flow (Distribute by percentage)
5% -> 25% -> 100%, weekly review of containment, repeat contact, CSAT, handoff reasons, guardrail
interventions. Owner: onshore AI lead; Pune team maintains the eval sets; monthly refresh with a frozen
holdout.

## 11. Cost per contact (illustrative prices)

| Contact type | Calculation | USD |
|---|---|---|
| Contained voice reset (2.0 min, 6 Lex requests) | 2.0 x 0.038 + 2.0 x 0.0022 + 6 x 0.004 + 0.0005 | 0.105 |
| Contained voice how-to (2.5 min, 5 Lex, 2 RAG turns) | 0.095 + 0.0055 + 0.020 + 2 x 0.0004 + model 0.0055 + guardrail 14 units x 0.0004 + 0.0005 | 0.133 |
| Contained chat how-to (12 msgs, 6 Lex text, 2 RAG) | 0.12 + 0.0045 + ~0.012 | 0.137 |
| Agent-handled voice with context (1.5 min bot + 6.4 min analyst) | 7.9 x 0.038 + 7.9 x 0.0022 + 0.016 + 6.4 x 0.85 | 5.78 |
| Agent-handled voice today (7.4 min, re-ask) | 7.4 x 0.038 + 7.4 x 0.0022 + 7.4 x 0.85 | 6.59 |
| Agent-handled chat (11 min, 2 concurrent, 30 msgs) | 5.5 x 0.85 + 0.30 | 4.98 |

Monthly at phase 3: voice 18,600 contained (2.2k) + 43,400 handled (250.9k) = 253.1k vs 408.6k today;
chat 15,200 contained (2.1k) + 22,800 handled (113.5k) = 115.6k vs 189.2k. Saving ~229k per month,
almost all analyst time. AI unit costs are noise: doubling model and guardrail prices adds ~0.01 per
contained contact. Sensitivity: every 10 points of voice containment ~= 35k per month (6,200 contacts x 5.66); the business
case rests on containment and the 60-70 s AHT saved by context, not on token prices. Agent assist and
Contact Lens features are part of Connect Customer channel pricing per the current pricing page
(verify before quoting).

## 12. Rollout, operations and team

Phase 1 (wk 1-8): reset/unlock/status on voice and chat, handoff contract, workspace view, ServiceNow
adapter. Phase 2 (wk 9-12): RAG how-to on chat (shadow, then 25%), agent assist for all queues.
Phase 3 (wk 13-16): RAG on voice, outage detection, 100% rollout after gates. Feature flags in flow
attributes from a Data Table so rollback is a config change. Monitoring: CloudWatch alarms on
ContactFlowErrors, Lambda errors/p95, Retrieve filtered=0 rate, guardrail intervention rate,
containment drop > 5 pts day over day. Runbooks per failure mode (Bedrock throttling -> force handoff
flag; ServiceNow down -> queue and create incidents later from CTR). RACI: onshore lead accountable
for design, security review and production readiness; Pune responsible for flows, Lambdas, IaC and eval
set upkeep; Monterrey responsible for UAT and analyst training; InfoSec consulted on guardrails and
entitlements; ServiceNow team responsible for KB hygiene. Hypercare 4 weeks with daily transcript review.

## 13. Decisions, risks and open questions

- D1 Retrieve + Converse in a Lambda over RetrieveAndGenerate or QnAIntent: needed for entitlement
  filters, citation checks, latency control; QnAIntent kept as an option for simple chat FAQs
  (supports `x-amz-lex:bkb-retrieval-filter`).
- D2 Managed KB with ServiceNow ACL crawl vs customer-managed KB with sidecars: spike in week 2.
- D3 Haiku-class model via US geographic inference profile: latency and residency; re-evaluate yearly.
- D4 Bedrock Agents Classic not used (closed to new customers); orchestration is our code plus Connect
  AI agents.
- Risks: KB quality (stale/duplicate articles) -> KB clean-up sprint with the ServiceNow team before
  phase 2; entitlement drift -> contract tests and alarms; analyst trust in summaries -> edit-before-save
  and feedback; quarter-end peaks -> load test at 1.35x.
- Open: OTP delivery channel for employees without MFA devices; whether email channel joins later.
