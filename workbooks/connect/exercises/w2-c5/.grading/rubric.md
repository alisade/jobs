# Rubric: connect/w2-c5 IVR and self-service journey redesign
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 0 | Does not apply: review-only design exercise (grade.sh reports 0/0) |
| 2 | Diagnosis from data | 15 | Full: quantifies time in IVR (~94 s), the employee-ID failure (31%/9%) and the fact it is not passed on, menus that route six branches to one skill, the impossible "reset online" advice, missing ticket status, Workday misroutes, queue and after-hours dead ends; uses the verbatims as evidence. Partial: qualitative only. |
| 3 | Journey design and VUI principles | 20 | Full: silent identification first, intent-first design with the frequent needs, short prompts, no dead ends, consistent DTMF; a clear journey map; sample prompts with before/after length. Partial: a re-ordered menu tree. Zero: keeps the 7-option menu. |
| 4 | Identity tiers | 15 | Full: ANI/portal identification, push verification for privileged self-service with timeout behavior (async Lambda + Wait within Connect limits), step-up for admin cases, no knowledge questions read back, no Voice ID (end of support). Partial: identification only. |
| 5 | NL vs DTMF and error handling | 10 | Full: open question with a DTMF safety net, confidence and reprompt rules, disambiguation, bounded no-input/no-match leading to an agent with context, barge-in. Partial: NL everywhere with no fallback. |
| 6 | Containment model | 15 | Full: per-driver self-service with a reasoned containment estimate (identification and enrollment rates), the weighted total against the 30% target, and containment defined with a repeat-contact check. Partial: a single target number. |
| 7 | Queue, callbacks, after-hours, accessibility, languages | 10 | Full: callbacks with a trigger, honest wait messaging, major-incident and after-hours paths, relay/TTY and timing, language memory and Spanish. Partial: two of these. |
| 8 | Measurement and implementation | 15 | Full: attributes set per step, dashboards, phased rollout or A/B with go/no-go, Connect implementation (flow modules, Lex intents and session attributes, Lambda budgets, what reaches the agent and ServiceNow, test plan). Partial: metrics without rollout or implementation detail. |
Total: 100
