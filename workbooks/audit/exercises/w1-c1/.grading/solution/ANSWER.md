# ANSWER: audit/w1-c1 Structured CM-03 evidence extraction

## Approach

The model reads messy evidence and returns typed facts with citations; code decides each attribute.
That split makes the conclusion reproducible (same facts, same result), explainable (each attribute
names the rule and the instants it compared) and testable without a model. The contract is strict
so that a missing or renamed key fails loudly instead of becoming a passing default.

## Fix

- contract.py: extra=forbid, no defaults, pattern for change ids, AwareDatetime, Literal sources, min lengths.
- extract.py: explicit config (temperature 0, JSON + schema, AFC off, two declared tools), a bounded
  tool loop with an allow-list, validation retry with the errors fed back, MAX_TOKENS retried, SAFETY not,
  id cross-check against the sample, usage summed.
- attributes.py: four rules over instants in UTC and directory-resolved identities.

## Trade-offs / what I would do in production

Log per call: model and model_version, a hash of system instruction + config + tool declarations,
the full request and response, usage, finish reason, retries and every tool call with arguments and
results. needs_review items go to a reviewer queue with the errors attached. Cost per sample comes
from usage (about 3 calls, ~2.7k input tokens). Before quarterly runs: evals on a labeled set,
a pinned model version, and a change ticket for prompt or model changes (ControlPilot is itself a
program change subject).
