# ANSWER: audit/ai-c1 GRC MCP server

## Approach

One server per engagement: build_server resolves the engagement once and every tool closes over it.
Four read tools shaped around audit tasks (what is in scope, the test record, what failed, what
evidence is filed) and one write. Errors are ToolErrors that tell the model what to do next.

## Fix

- server.py: the four tools with read-only annotations and model-oriented descriptions; opaque cursors
  bound to the query and status; record_exception with the write annotation, token verification, SoD,
  duplicate check, and no write on any rejection.
- tokens.py: canonical JSON payload, HMAC-SHA256, constant-time compare, malformed/signature/expired/scope errors.

## Trade-offs / what I would do in production

A prompt rule or an annotation is not a control: injected text can talk a model past a rule, and any
MCP host can call any tool. A signature over a key the agent never sees can't be faked. For real:
streamable HTTP with OAuth, the key in Key Vault with a key id for rotation, 15-minute tokens recorded
as used to stop replay, and an audit record per call with caller, arguments, result and token id.
