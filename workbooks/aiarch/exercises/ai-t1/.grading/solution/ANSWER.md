# ANSWER: aiarch/ai-t1

## Approach

Compared usage blocks before and after 3.1.0, then read the builder against the stub's caching
rule (prefix up to the last cachePoint).

## Root cause

3.1.0 appended "Current time ... Request id ... Signed-in user ..." to the system prompt text,
which sits before the cachePoint. That text differs on every request, so the cached prefix is
never identical: every turn writes the cache and none reads it. Evidence: after the release
every usage block has cacheWriteInputTokens 2180 and cacheReadInputTokens 0 (before: one write,
then reads of 2152); daily-cost shows cache reads dropping to 0 and writes rising to 19.8M
tokens from 2026-11-10, and cache writes cost more than plain input.

The minimum-size theory does not fit: 2180 tokens are written, so the prefix is above the
minimum (below it nothing would be written). The TTL theory does not fit: turns arrive every
few seconds, and even back-to-back turns miss.

## Fix

System prompt alone before the cachePoint; tool specs sorted by name; the time, request id and
user move into a context block in the turn's user message, before the question. Verified with
make test: reads from turn 2 and across users, cost under budget.

## Trade-offs / what I would do in production

- Alarm on cache read ratio (cacheReadInputTokens over total input) per application inference
  profile, and keep cost per conversation on the AgentOps dashboard.
- A unit test that two requests have byte-identical prefixes catches this before release.
- Dynamic data in the user turn costs a few uncached tokens per request, which is the point.
