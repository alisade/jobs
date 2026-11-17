# ANSWER: aiarch/ai-c1

## Approach

Four tools shaped around what an agent does with changes, not around the REST endpoints.
Identity is bound once per session: build_server verifies the token and the tools close over
the verified caller, so no argument can change who the server acts as.

## Fix

Pydantic-typed arguments (Literal risk, patterned ids, length limits, timezone-aware datetime)
reject bad input before the backend is called; CMDB checks with close-match hints; trimmed
outputs; opaque cursor pagination; owner-group check on comments; read-only annotations on the
two read tools. Verified with make test.

## Trade-offs / what I would do in production

Five rules from daily MCP use:
1. Small outputs: get_change returns a comment count, not comment bodies.
2. Errors the model can act on: unknown service lists close matches; bad cursor says what to send.
3. Identity from the token, never from arguments: no requester parameter exists.
4. Paginate lists: five per page with next_cursor.
5. Mark read-only tools so clients can auto-approve them and gate writes.

Deployment: run it on AgentCore Runtime with the MCP protocol contract (Streamable HTTP) and add
it to the gateway as an MCP server target, so inbound JWT, Cedar policy and logging are shared
with the other tools. The server validates the token audience itself and calls the change API
with an OBO-exchanged token, never the client's token. Add a tool-choice eval to CI.
