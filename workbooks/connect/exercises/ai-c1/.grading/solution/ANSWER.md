# ANSWER: connect/ai-c1 Guarded LLM triage with an eval gate

## Approach

Wrote the request contract first (static system prompt, fenced transcript, guardrail, temperature 0,
300 tokens), then strict parsing with fallbacks, then deterministic guards, then the eval metrics; used
make test for each step and make eval at the end.

## Fix

triage: AbortController budget (2.5 s inside the flow's 4 s), fallbacks for timeout/error/guardrail/invalid
output, enum validation, fence handling, extra fields dropped, P1 only for outages with an outage signal,
injection regex -> human + P3, SSN/URL scrubbing, flat string attributes. eval: accuracy, schema-valid,
fallback, injection containment, priority ceilings, per-category, failures, gate with reasons.
make eval: accuracy 0.75, fallbackRate 0.25, injectionPassRate 1 -> GATE: FAIL.

## Trade-offs / what I would do in production

Do not ship: define categories with examples (VPN -> software), shorten the summary or use tool use
for structured output, re-record, re-run. Grow the red-team set; monitor fallback rate and sample
transcripts weekly. The regex injection check is a tripwire, not a control; the controls are the
boundary, the guardrail and code deciding priority.
