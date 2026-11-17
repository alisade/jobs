# genai/w5-c1 - Service boundaries for the shopping assistant: three ADRs

**Type:** design | **Estimate:** 2-2.5 hours | **Study plan:** Week 5 (microservices boundaries,
sync vs async, resilience patterns, ADRs); Week 3 (streaming, retries and fallbacks)

## Scenario

Kestrel Outfitters' architecture review board meets on Thursday to approve the shopping assistant for
the holiday season. The AI team (four engineers, including you) has a working prototype, but three
decisions are still open and every lead in the room has an opinion. Should the assistant be its own
service or part of the storefront? How do answers stream through the existing CDN and API gateway?
Where do model fallback and rate limits live? You write the ADRs and defend them.

## What you have

| Path | What it is |
|---|---|
| `inputs/requirements.md` | capabilities, traffic (holiday peak 12x), latency and cost targets, teams |
| `inputs/current-architecture.md` | the storefront monolith, catalog and order services, CDN, Kong |
| `inputs/incident-history.md` | the three incidents the board will bring up |
| `inputs/constraints.md` | security and platform constraints, the Q4 change window |
| `DESIGN.md` | the template you fill in (the deliverable) |
| `ANSWER.md` | approach, key decisions, trade-offs |

## Your task

1. Fill in every section of `DESIGN.md`. Write three ADRs (context, options considered, decision,
   consequences, revisit when):
   - ADR-1: the assistant as a separate service or a module in the storefront, and catalog access through
     its API or its database.
   - ADR-2: the streaming transport (SSE, WebSocket or polling) through the existing gateway and CDN.
   - ADR-3: model fallback and rate limiting inside the assistant or in a shared LLM gateway.
2. Add a system diagram, a "how it fails" table and a latency/cost budget.
3. Record the options you rejected and why. The board cares about those as much as the decision.
4. Summarize your key decisions in `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- Graded by rubric only: `grade.sh` prints a completeness report and `GRADE_TESTS {"passed": 0, "total": 0}`;
  the rubric's automated row does not apply.
- Each ADR weighs at least two real alternatives against the inputs (peak, TTFT, cost, ownership,
  team size, incidents, constraints) and names its consequences honestly, including the bad ones.
- Data ownership, fail-soft behaviour and the security constraints are respected.
- The failure table covers provider outage, rate limits, slow dependencies, assistant down and peak load.

## How to run

```bash
make test        # completeness report: which DESIGN.md / ANSWER.md sections are still empty
# from workbooks/ in Claude Code: /grade genai/w5-c1
