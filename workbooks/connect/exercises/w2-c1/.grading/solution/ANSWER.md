# ANSWER: connect/w2-c1 Erlang C staffing calculator

## Approach

Replaced the factorial Erlang C with the Erlang B recursion and derived C from it; checked values
against the textbook example (14 agents, 88.8% in 20 s, ASA 7.8 s) and a 500-Erlang case.

## Fix

Defined unstable-queue and zero-load behavior; search starts above the load and at the occupancy
floor; concurrency as slots; shrinkage divides; RangeError on bad input and impossible ceilings;
staffingPlan per interval. Monday: peak 37 scheduled, 295.5 agent-hours. AHT 432 s: peak 43 (+6),
338 agent-hours (+14%).

## Trade-offs / what I would do in production

Erlang C ignores abandons and retrials, assumes Poisson arrivals and one skill; use Erlang A or
simulation for multi-skill proficiency routing; chat concurrency is optimistic. Production schedules
come from Connect forecasting and agent scheduling; this model sanity-checks and explains them.
