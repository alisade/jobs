# Reference: modernize/ai-c1

`.grading/solution/pod_agent/loop.py`: every tool call goes through `_call`, which validates the input with
jsonschema, scopes the path with `resolve()` + `relative_to` (defeats `..`, absolute paths and symlinks),
denies secret reads (also filtering `search` hits), allows writes only to `src/main/**` and `pom.xml` before
asking the reviewer, turns every failure into an `is_error` result with an actionable message, truncates
large output with a marker, caps turns, and records an audit entry per call.

Key point for interviews: the injection succeeds at the model level (the scripted model does follow it), and
nothing happens anyway, because the controls are in the harness. That removes the private-data leg
(secrets unreadable) and the action leg (tests unwritable); in CI you would also remove the exfiltration leg
(no egress, no secrets in the environment).
