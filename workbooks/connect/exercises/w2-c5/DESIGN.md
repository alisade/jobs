# LFG Service Desk IVR and self-service journey redesign

Author: <you>        Version: 0.1

<!-- Audience: the service owner, the UX/VUI reviewer and the offshore flow developers. Use the data
in inputs/. Show the numbers behind every change. Diagrams in ```text or ```mermaid blocks. -->

## 1. Goals and success metrics

<!-- The targets (containment, time to agent, zero-out, CSAT) with today's baselines and how each is
measured (definitions!). -->

## 2. Diagnosis of the current IVR

<!-- What the data and verbatims say: where time is spent, where callers fail or zero out, what is
misrouted, what is impossible today. Quantify. -->

## 3. Design principles

<!-- 5-8 VUI principles you will hold the design to (e.g. identify silently first, most frequent intents
first, never dead-end, always a way to a human, short prompts, consistent DTMF). -->

## 4. Target journey map

<!-- Diagram of the new journey from entry to resolution or agent, per channel (voice; chat entry from
the portal). Mark where identity, intent, self-service and handoff happen. -->

## 5. Identification and authentication tiers

<!-- How a caller is identified without typing (ANI), when and how verification happens (push), what each
tier unlocks, what happens when it fails. -->

## 6. Natural language vs DTMF

<!-- Where you use an open "how can I help" (Lex), where DTMF menus, and the fallback rules between them.
Confidence handling, disambiguation, no-input/no-match strategy. -->

## 7. Containment and deflection by driver

<!-- Table per driver: self-service path, expected containment with reasoning, deflection to chat/portal,
what context goes to the agent when it fails. -->

## 8. Queue experience: callbacks and queue-in-place

<!-- When to offer a callback, what the caller hears, position/wait messaging, VIP and major-incident
treatment, after-hours. -->

## 9. Prompts (sample script)

<!-- The greeting, the open question, two self-service turns, the handoff line. Show before/after length
in seconds or words. -->

## 10. Accessibility and languages

<!-- TTY/relay, timing, DTMF everywhere, language memory, Spanish journeys. -->

## 11. Measurement and experimentation

<!-- Instrumentation (contact attributes you set at each step), dashboards, A/B or phased rollout plan,
how you will know containment is real (repeat contacts!). -->

## 12. Implementation notes in Amazon Connect

<!-- Flows and flow modules, Lex intents and slots, Lambdas and their time budgets, attributes passed to
the agent and ServiceNow, what you test before go-live. -->

## 13. Risks and open questions
