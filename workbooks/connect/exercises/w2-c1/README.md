# connect/w2-c1 - Erlang C staffing calculator

**Type:** coding | **Estimate:** 1.5-2 hours | **Study plan:** Week 2 (Thu: workforce and capacity planning, Erlang C)

## Scenario

LFG's steering committee asked a simple question during the business case review: "How many
agents do we need on Monday, and what happens to service level if AHT goes up by a minute?"
The WFM analyst's answer came from a spreadsheet macro that was ported to TypeScript for the
planning service (`src/erlang.ts`). It "works for small teams": on the full help desk forecast
it returns `NaN`, it sometimes recommends fewer agents than the load, and shrinkage is applied
the wrong way. Forecasting and agent scheduling in Amazon Connect (formerly forecasting, capacity
planning and scheduling) will own production schedules, but the transformation team needs an
independent, explainable model for the design document, for what-if analysis on chat
concurrency and for sanity-checking the vendor numbers.

## What you have

| Path | What it is |
|---|---|
| `src/erlang.ts` | the planning module: exported signatures are fixed, the internals are not |
| `inputs/forecast-monday.json` | LFG voice forecast: 28 half-hour intervals, AHT 372 s, 80% in 30 s, max occupancy 85%, shrinkage 32% |
| `tests/erlang.test.ts` | visible tests (textbook example: 100 calls / 30 min, AHT 180 s, 80/20) |

## Your task

1. Implement Erlang B with the stable recursion and Erlang C from it; no factorials or powers
   that overflow (a 500-Erlang center must work).
2. `serviceLevel`, `averageSpeedOfAnswer`, `occupancy`: correct for stable queues, and defined
   behavior for unstable ones (agents <= load: wait probability 1, SL 0, ASA Infinity) and for
   zero traffic.
3. `agentsRequired`: smallest staffing meeting the SL target, honoring an optional occupancy cap
   and chat `concurrency` (servers = concurrent contact slots; agents = ceil(slots / concurrency)),
   then `scheduled = ceil(agents / (1 - shrinkage))`. Validate inputs (`RangeError`), and fail
   loudly when `maxAgents` cannot meet the target.
4. `staffingPlan(forecast)`: per-interval results, the peak scheduled headcount and the total
   scheduled agent-hours.
5. In `ANSWER.md`, use your model to answer: Monday peak headcount and agent-hours; what an
   extra 60 s of AHT does to the peak; and the limits of Erlang C you would flag to the steering
   committee.

## Acceptance criteria (what the grader checks)

- Erlang B/C, SL, ASA and occupancy match independently computed values to 4-5 decimals,
  including a 500-Erlang center.
- Edge cases: unstable queues, zero traffic, tiny load, invalid input, impossible ceiling.
- Occupancy cap, shrinkage and chat concurrency applied as specified.
- The Monday plan matches the reference interval by interval (peak and agent-hours).
- `ANSWER.md` answers the three questions with numbers and names Erlang C's assumptions.

## How to run

```bash
make setup     # links the shared toolchain
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w2-c1
make clean
```
