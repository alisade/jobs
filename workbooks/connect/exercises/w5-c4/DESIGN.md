# Design: AI-assisted help desk self-service and agent assist (LFG)

<!-- Fill every section. Keep it to what a design review with InfoSec, the ServiceNow team and the
offshore build team needs. Diagrams as ASCII or mermaid in fenced blocks. Cite the inputs/ files
for numbers you use. -->

## 1. Goals and success metrics

<!-- Business goals, baseline from inputs/current-state.md, targets per phase: containment by driver,
transfer-with-context rate, AHT on transferred contacts, CSAT, hallucination/escape rate. -->

## 2. Use cases and channel scope

<!-- Table: driver -> self-service (voice/chat) or agent assist or out of scope, and why. -->

## 3. Architecture

<!-- Diagram + component list: Connect flows, Lex V2 bot(s), Lambdas, Bedrock (Converse, Knowledge Base,
Guardrails), AI agents (formerly Amazon Q in Connect), ServiceNow, Okta, data stores, logging.
Say which pieces are managed features vs your code, and what runs in which region. -->

## 4. Conversation design and bot-to-agent handoff

<!-- Voice and chat journeys for the top drivers, identity verification tiers, the handoff contract
(attributes, summary) and how it reaches the agent workspace and the ServiceNow incident. -->

## 5. Knowledge and retrieval

<!-- Source of truth, sync path (connector or exporter), chunking, metadata and entitlement filtering
(restricted HR/Legal/Finance, contractors), freshness and retired articles. Managed vs customer-managed
knowledge base decision. -->

## 6. Safety, privacy and compliance

<!-- Guardrails policies and thresholds, PII handling in prompts/transcripts/logs, prompt injection
(caller speech and documents), model invocation logging, retention (13 months), data residency. -->

## 7. Agent assist and agent workspace

<!-- AI agents for real-time recommendations and knowledge search, generative summaries for after-contact
work, what the analyst sees on handoff, supervisor tools. -->

## 8. ServiceNow integration

<!-- Incident/request creation and lookup, idempotency, work notes, KB sync, auth (OAuth client credentials). -->

## 9. Latency budget

<!-- Per voice turn: ASR/Lex, Lambda, Retrieve, model, guardrail, TTS. Synchronous vs async Lambda mode,
holding prompts, timeouts and fallbacks. -->

## 10. Evaluation plan

<!-- Offline eval sets (intent, retrieval, answer faithfulness, citation precision), red team, Lex Test
Workbench, pre-production gates, online metrics and A/B, ownership and cadence. -->

## 11. Cost per contact

<!-- Use inputs/prices.md (illustrative; say so). Cost per contained voice contact, per contained chat,
per agent-handled contact with assist; monthly totals and savings vs today; sensitivity to the big drivers. -->

## 12. Rollout, operations and team

<!-- Phases over 16 weeks, feature flags/percentage splits, monitoring and alarms, runbooks, on-call,
RACI with the Pune and Monterrey teams, hypercare. -->

## 13. Decisions, risks and open questions

<!-- ADR-style list: decision, options considered, why. Top risks with mitigations. -->
