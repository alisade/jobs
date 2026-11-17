# ANSWER: edgefde/ai-c1 Operator assistant on a local model

## Approach

Wrote the contract and tools first, then the loop against the visible scenarios, then each failure
scenario (bad JSON, fake citations, unknown tools, endless tool calls), then the router.

## Fix

Everything that matters is enforced in code, not asked for in the prompt: Pydantic validates the
answer and the action enum (no state-changing action exists), citations must be ids of tool calls
executed in this conversation, the dispatcher only runs allowed tools and returns errors as data, and
the cloud run is built without local-only tools so raw samples cannot be requested or returned. A bad
reply gets one retry with the validation error in the message; small models usually fix the JSON when
told exactly what failed.

## Trade-offs / what I would do in production

Run the same scenarios against the real local model (for example an 8B model in Q4 under llama.cpp)
and record accuracy and latency per answer on the plant server; the cloud fallback is worth it only if
it fixes failures the local model cannot. The cloud flag belongs to OT security, with the endpoint on
the proxy allow-list. Add OTel spans per model and tool call, and injection tests on alert notes.
