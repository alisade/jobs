# ANSWER: modernize/ai-c1 A guarded migration agent

## Approach

Wrote the adversarial runs first as scripted models (the injection, escapes, floods), then put every
control in one function at the tool boundary so no path bypasses it.

## Fix

- Schema validation with jsonschema; unknown tools and invalid input become `is_error` results that
  say what to do instead.
- Path containment by resolving and checking `relative_to(root)`, which also catches symlinks.
- Secrets deny-list on reads and on search hits.
- Write allow-list (`src/main/**`, `pom.xml`) checked before the reviewer is asked; the reviewer only
  sees patches that are allowed at all.
- Truncation with a marker, `max_turns`, one audit entry per call.
The system prompt says "never edit tests", but that is guidance; the injection test shows the model
following the planted note and the harness refusing anyway.

## Trade-offs / what I would do in production

The lethal trifecta: secrets (private data) are unreadable, the notes file is untrusted content we
cannot avoid, and in CI I would remove the exfiltration channel too: ephemeral container, no secrets
in the environment, egress only to the model endpoint, checkout read-only outside src/main. Limit
patch size to keep reviews real, and run these adversarial scenarios as evals on every prompt or
tool change.
