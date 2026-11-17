# connect/w5-c4 - Design an AI-assisted help desk (self-service + agent assist)

**Type:** design | **Estimate:** 3 hours | **Study plan:** Week 5 (all days; capstone for Lex, Bedrock, Guardrails, AI agents, ServiceNow)

## Scenario

LFG's steering committee approved the move to Amazon Connect but not the AI features: the Lex pilot
contained 9% of calls, every transfer arrived without context, and InfoSec has three conditions
(no restricted HR/Legal/Finance content to unentitled people, no PII in prompts beyond employee ID,
proof of prompt-injection testing). The budget owner wants a cost per contact model. You are the
lead architect: write the design that goes to the design review with InfoSec, the ServiceNow team and
the Pune build team.

## What you have

| Path | What it is |
|---|---|
| `inputs/current-state.md` | volumes, call drivers, AHT, pilot results, team |
| `inputs/constraints.md` | security, records, residency, identity, latency, accessibility, timeline |
| `inputs/prices.md` | unit prices for the cost model - illustrative, verify before real use |
| `DESIGN.md` | the template you fill in (13 sections) |

## Your task

Fill in `DESIGN.md`: goals and metrics, use-case scoping, architecture (diagram), conversation design
and the bot-to-agent handoff contract, knowledge and retrieval with entitlements, safety and
compliance, agent assist and workspace, ServiceNow integration, latency budget, evaluation plan,
cost per contact, rollout and team, decisions and risks. Then summarize in `ANSWER.md`.

Use current names and capabilities (check the week 5 study guide): Amazon Connect Customer, AI agents
(formerly Amazon Q in Connect), Bedrock Knowledge Bases (managed and customer-managed), Guardrails,
Lex V2 generative features. Do not invent features; say "verify" where you are unsure.

## Acceptance criteria (what the grader checks)

Graded by rubric only (no automated tests; `grade.sh` prints a completeness report and
`GRADE_TESTS {"passed": 0, "total": 0}`):

- Use cases scoped by driver with baselines and phase targets.
- Correct, current architecture; managed vs custom pieces named.
- An explicit handoff contract that reaches the agent workspace and ServiceNow.
- Entitlement-aware retrieval, guardrail policies, injection handling, logging and retention.
- A latency budget under Connect's 8 s synchronous limit with fallbacks, and an evaluation plan with gates.
- A cost per contact model from the inputs with sensitivity.
- A phased delivery plan with RACI for the offshore team, decisions and risks.

## How to run

```bash
make test      # completeness report: which sections are still empty
# from workbooks/ in Claude Code: /grade connect/w5-c4
```
