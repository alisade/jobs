# ANSWER: fde/x-1 Halyard risk-API client

## Approach

<!-- Token cache and single flight, where the budget wraps, how errors are mapped, how the
breaker is wired into assess, and how you tested the concurrency claims. -->

## Fix

<!-- Coding exercise: summarize the change set (files, key functions) and the tests you
added beyond the visible ones. -->

## Trade-offs / what I would do in production

<!-- Short. E.g. consecutive-failure vs rate-based breakers, per-process vs shared breaker
state across workers, retries vs budget, token refresh in the background, metrics you would
emit (breaker state changes, budget exhaustion, token fetch latency). -->
