# connect/w2-c2 - Routing simulator: tune the LFG routing design

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 2 (Wed: routing strategy; Thu: capacity planning); Week 1 (Wed: routing mechanics)

## Scenario

LFG's routing design for the Monday peak (four queues, four routing profiles, 36 agents) was
built by translating Avaya skills one to one. In the design review the offshore team lead
asked the question nobody could answer with Erlang C: "what happens to VIP and SAP calls when
the apps team also takes general overflow?" Erlang C (w2-c1) assumes one skill and infinite
patience, so the transformation team wants a small deterministic simulator of Amazon Connect's
routing behavior to compare designs before they are configured: routing-profile queue priority
and delay, contact priority and queue time adjustment, proficiency-based routing criteria with
expiring steps, and callers who hang up.

The routing team's first cut (`src/sim.ts`) is FIFO across everything and gets every one of
those wrong.

## What you have

| Path | What it is |
|---|---|
| `src/types.ts` | config, contact and report shapes (fixed) |
| `src/generate.ts` | deterministic contact stream generator (mulberry32 seed); given |
| `src/sim.ts` | the simulator to rewrite (`simulate`, `activeStep`, `agentMatches`) |
| `inputs/stream-spec.json` | Monday 08:00-10:00 peak: password reset, general, SAP apps (with routing criteria), VIP |
| `inputs/lfg-config.json` | today's routing design (queues, profiles, 36 agents with proficiencies) |
| `inputs/tuned-config.json` | your improved design (starts as a copy of today's) |
| `scripts/run.js` | `make baseline` / `make run` print the report for a design |

## Semantics to implement (a model of Connect routing, stated precisely so it is testable)

Time advances in whole seconds. At each second `t`, in this order:

1. Agents whose contact ends at `t` become available; they have been idle since `t`.
2. Contacts arriving at `t` join their queue.
3. Waiting contacts with `arrival + patience <= t` abandon.
4. Routing: available agents, longest idle first (ties by agent id), each take the best eligible
   waiting contact; repeat until nobody can take anything.

A contact is eligible for an agent when the agent's routing profile contains the contact's
queue, the contact has waited at least that profile's `delaySeconds` for the queue, and the
agent satisfies the contact's active routing-criteria step (all conditions, proficiency level
at or above `minLevel`). Steps are active for `expirySeconds` each, cumulatively; a step without
`expirySeconds` never expires; once every step has expired, any agent on the queue qualifies.
Best contact = lowest profile priority number, then lowest contact priority (default 5), then
earliest `arrival - timeAdjustmentSeconds`, then id.

Metrics: service level = answered within the threshold (wait `<=` threshold) / offered, so
abandons count against you (1 when nothing was offered); ASA = mean wait of answered contacts;
abandon rate = abandoned / offered; occupancy = busy seconds / horizon, where the horizon is the
second the last contact finished or abandoned. Invalid configs (unknown queue or routing profile,
duplicate contact ids, bad times) throw.

## Your task

1. Rewrite `src/sim.ts` to these semantics. It must be deterministic, must not mutate its inputs,
   and must handle 20,000 contacts in a few seconds (skip idle seconds; do not tick every second).
2. Tune the design in `inputs/tuned-config.json`: same agents, proficiencies and queues; you may
   change routing profiles (queues, priorities, delays) and which profile each agent has. Targets
   on the published stream: every queue >= 80% in 30 s, VIP >= 90%, overall abandon <= 6%.
3. In `ANSWER.md`: the baseline numbers, what you changed and why (in Connect terms), and how you
   would check the design is robust (other seeds, +10% volume, AHT drift) before configuring it.

## Acceptance criteria (what the grader checks)

- Hand-built scenarios for each rule: FIFO, abandon timing, profile priority over age, delay,
  criteria step expiry and fallback, longest-idle agent, contact priority, time adjustment,
  abandon-before-route, SL with abandons in the denominator, occupancy over the horizon.
- Baseline figures on the published stream match the reference semantics exactly.
- Validation, determinism, no input mutation, 20,000 contacts in under 5 s.
- Tuned design meets the targets with the same agents and proficiencies.

## How to run

```bash
make setup
make baseline                 # today's design on the published stream
make run                      # your tuned design; make run SEED=7 to try another stream
make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w2-c2
make clean
```

This is a model, not Connect: Connect also has agent statuses, after-contact work, callbacks,
multi-channel concurrency and cross-channel routing. Say in ANSWER.md which ones matter for LFG.
