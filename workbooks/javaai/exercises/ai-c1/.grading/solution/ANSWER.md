# ANSWER: javaai/ai-c1 Read-only learner-progress MCP server

## Approach

Started from what the tutor needs (where is the learner, which lessons exist, what does a lesson say)
rather than from the REST endpoints. Removed record_mastery and the learner_id argument entirely.

## Fix

Three read-only annotated tools bound to the session learner, enrollment checks on every call,
reshaped outputs without answers or email, lesson text capped at 1500 characters with HTML comments
stripped and labelled untrusted, outage mapped to an "unavailable, retry" error. 11/11 tests.

## Trade-offs / what I would do in production

ADK connects with McpToolset (stdio locally, streamable HTTP on Cloud Run with ID-token auth) and a
tool_filter as a second layer. The learner comes from the authenticated session, never from the
model, which avoids the confused-deputy problem. The untrusted label helps the agent's callbacks but
the real control is that no write tool exists here.
