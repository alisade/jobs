# Reference: aiarch/ai-t1

Root cause: 3.1.0 put the timestamp, request id and user into the system text before the
cachePoint, so the prefix hash changes every request (write every turn, never read). Fix: static
system prompt and sorted tools before the cachePoint, dynamic context in the user turn.
