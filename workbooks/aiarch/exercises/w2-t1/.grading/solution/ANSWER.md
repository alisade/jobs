# ANSWER: aiarch/w2-t1

## Approach

Read the page and release notes, then the per-turn logs, then `service/app.py`.

## Root cause

Release 2.3.0 "reuse the specialist Agent" made the specialist a module-level singleton
(`_SPECIALIST` in `service/app.py`). Every request in the process uses the same Strands Agent,
and an Agent keeps its message history, so manager B's turn is sent to the model together with
manager A's conversation and tool results. Evidence: in `incident/app-logs.jsonl` every turn
from every session and user has the same `agent_object_id` (0x7f3e2c1a9d50) and
`messages_in_context` grows by 4 per turn across sessions, as does
`gen_ai.usage.input_tokens`; the transcript for sess-91c2 contains lwong's payments data that
only sess-7f1a fetched. Tokens reset at 02:00 because the deploy restarts the process. The
singleton was also built with the first caller's team tools.

Temperature and prompt are red herrings: the data the model repeated was really in its
context, and no prompt can make a model forget what it was sent.

## Fix

A per-session registry: `OrderedDict` of session id to (Agent, last use, team), LRU-bounded by
`max_sessions`, entries idle longer than `idle_seconds` evicted, a lock for the registry and one
lock per session so two turns of the same session do not interleave. Verified with `make test`.

## Trade-offs / what I would do in production

- On AgentCore Runtime each session gets its own microVM, which isolates sessions if the code
  keys state on the session; process globals are still shared by all requests a microVM serves.
- For durable continuity use a Strands session manager backed by S3 or AgentCore Memory keyed
  on the session id rather than in-process state.
- Add the isolation test to CI and log a hash of the session id with the agent object id so
  this is visible on a dashboard.
