# Reference: aiarch/w4-t1

Root cause: Cedar skips a policy whose evaluation errors. policy2 reads principal.team; partner
tokens have no team, so policy2 errors, policy1 permits. The LOG_ONLY review missed the errors
field (AR-1102). Fix: `principal has team && principal.team == context.input.team`. The
schema has team optional, so strict validation flags the unguarded access.
