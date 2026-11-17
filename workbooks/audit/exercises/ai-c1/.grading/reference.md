# Reference: audit/ai-c1

Reference files: `.grading/solution/grcmcp/server.py` and `tokens.py`.

- **Scoping.** `build_server` resolves the engagement once and every tool closes over it, so there is
  no argument a model could use to reach another engagement. Unknown ids get a ToolError that lists
  the valid ids and points to `list_controls`.
- **Errors.** In mcp 2.x a plain exception from a tool is masked as "Error executing tool X"
  (`UnexpectedToolError`), so the model cannot recover; `ToolError` keeps the message. Argument
  validation errors from the generated Pydantic model are reported the same way.
- **Pagination.** An opaque base64 cursor carrying offset, query and status; rejecting a cursor from a
  different query prevents silent skips or repeats when the model changes the filter mid-walk.
- **Gate.** The token is signed by the review service (HMAC over the canonical payload; constant-time
  compare), bound to engagement, control, sample, reviewer and expiry, and the server enforces
  reviewer != preparer and no duplicates. Annotations (`readOnlyHint`) are hints for the host, not
  controls; a prompt rule can be overridden by injected text. The only thing an agent cannot fake is a
  signature over a key it never sees.
- **Production.** Streamable HTTP transport with OAuth (the MCP authorization spec), the HMAC key in
  Key Vault with a key id in the token for rotation, short expiry plus a used-token table for replay,
  and an audit record per tool call (caller identity, arguments, result, token id).
