# ANSWER: javaai/x-2 Flow metrics and a Monte Carlo forecast

## Approach

Implemented the flow metrics first and checked them on hand cases (week boundaries, percentiles), then
the seeded simulation with a cap and an all-zero guard.

## Fix

    weekly throughput: [7, 4, 4, 4, 5, 0, 7, 8, 4, 3, 6, 5]
    50%: 2026-12-28   85%: 2027-01-04   95%: 2027-01-11
    items in 4 weeks at 85%: 15;  cycle time p50/p85: 6 / 12 days
10/10 tests.

## Trade-offs / what I would do in production

To the product lead: 85% by 4 January, 50% by 28 December; commit to 15 items in the next 4 weeks. The
zero week stays in the sample because holidays and conferences recur. The forecast breaks if scope
grows, WIP rises or items are split; re-run it every Monday. For AI work, time-box spikes and define done
as an eval threshold so items do not stay open indefinitely.
