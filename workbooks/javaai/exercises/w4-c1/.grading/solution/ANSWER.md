# ANSWER: javaai/w4-c1 Tutor agent service

## Approach

Treated three boundaries separately: the caller (ID token), the model's tool requests, and the
model's final text. Each became code with a test: auth dependency, allow-list with session-bound
runners, before/after guards, and a bounded loop.

## Fix

auth.py verifies RS256, audience, issuer, expiry and the caller allow-list (401 vs 403). app.py
uses it as a dependency and validates message length. agent.py offers and runs only the two read
tools, drops model-supplied learner/course ids, returns errors to the model, stops after 4 tool
calls, refuses off-topic messages before the model and withholds replies containing the current
quiz answer. 23/23 tests pass.

## Trade-offs / what I would do in production

In ADK these are before_model_callback, after_model_callback and the tool list (tool_filter on an
McpToolset). They are code because a prompt can be overridden by injected content. Cloud Run IAM
(roles/run.invoker for the catalog SA only) is the first layer; google-auth verification with
cached certs is the second. The keyword topic guard will refuse some valid questions; track refusal
rate and move to a small classifier if it is too strict.
