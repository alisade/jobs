# ANSWER: modernize/ai-t1 Prompt caching never hits

## Approach

Started from the dashboard: request and token counts are flat, but from 2026-11-06 cache_read is 0
and cache_creation is about 11M tokens a day (it was 1.4M). So the prefix changes every request.
Then the git log for that day, then `make replay`.

## Root cause

Commit 7a1c9e2 (2026-11-05 16:12) put `Current time: ...` with seconds inside the system block that
carries `cache_control`. The cached prefix must match byte for byte, so every turn writes about 32k
tokens and none reads: `make replay` shows cache_write 32514 and cache_read 0 on all 8 turns, 1.03 USD
for the session. 11M write tokens a day at 3.75 per million is about 41 USD, which is the jump from
10 to 43 USD a day. Two latent problems break sharing across CI jobs: the file listing is joined from
a set (POD-209; Python randomizes string hashing per process) and the skills come in glob order
(POD-207). Not the model bump: same prices per the pricing note, merged at 11:03 before the cache
broke, and input and output token counts did not move.

## Fix

The static block (instructions, sorted listing, skills sorted by name) carries the breakpoint; the
time goes in a second system block after it. Verified: replay now writes once and reads on turns
2-8 (0.24 USD), and the tests show the prefix is identical across times, orders and processes.

## Trade-offs / what I would do in production

Guard in CI: build two requests with different times and shuffled inputs and assert the prefix
hash is equal; alert when cache-read share drops below 60% for a day. Review any change to the
prompt builder for per-request data before the breakpoint (timestamps, run ids, random ordering).
For long sessions, add a second breakpoint on the conversation history and keep turns inside the
cache TTL.
