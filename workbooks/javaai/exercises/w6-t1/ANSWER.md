# ANSWER: javaai/w6-t1 The Recent activity card got slow

## Approach

<!-- How you investigated: what you looked at first, what you ruled out and how. -->

## Root cause

<!-- The mechanism with evidence (plans, rows removed by filter, growth). Why the existing index does
not help. Why VACUUM did not. -->

## Fix

<!-- Migration and query change; plans before and after; how you proved results are unchanged. -->

## Trade-offs / what I would do in production

<!-- Short. CREATE INDEX CONCURRENTLY, write amplification of another index on a hot table, whether
idx_attempt_created_learner is still needed (nightly export), partitioning quiz_attempt by month,
a plan-regression check in CI. -->
