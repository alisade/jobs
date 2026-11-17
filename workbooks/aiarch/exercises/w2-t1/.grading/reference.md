# Reference: aiarch/w2-t1

Root cause: `_SPECIALIST` module global (release 2.3.0 optimisation) shares one Strands Agent
and its message history across every session in the process; built with the first caller's team
tools too. Evidence: constant agent_object_id, growing messages_in_context and input tokens,
transcript with another session's data. Temperature 0.7 and the prompt are red herrings. Fix:
session-keyed registry with LRU bound, idle expiry and per-session locks (see solution).
