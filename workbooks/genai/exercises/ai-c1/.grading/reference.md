# Reference: genai/ai-c1

Solution: `.grading/solution/associate_mcp/server.py`.

- **Task-shaped tools.** Each description says what the tool is for and what to do with its output, for
  example "Use the SKU with store_stock or prepare_hold". Inputs are `Annotated[..., Field(...)]`, so
  the JSON schema carries limits and patterns and the SDK rejects bad input before your code runs.
- **Compact output.** Only the fields an associate needs. `more_results` plus a hint keeps the context
  small and tells the model how to refine the query.
- **Least privilege.** Write tools are not registered without `write_scope`, because a tool the model
  cannot see is safer than a tool that refuses. The store scope comes from the server's identity,
  not from tool arguments. "Not at your store" and "missing" return the same error. Orders return a
  first name and initial only.
- **Two-step write.** `prepare_hold` validates and issues a short-lived single-use token with a
  human-readable summary. The host shows the summary to the associate before calling
  `hold_item_for_customer`. Stock is re-checked at confirm time.
- **Audit.** Every call is logged with success or failure, and the token is truncated in the log.

Production: run over streamable HTTP behind OAuth (MCP authorization spec). Derive the associate's
store from the token's claims. Rate-limit per associate. Write audit records to an append-only store.
Keep an eval set of associate questions scored on tool choice and arguments, and re-run it whenever a
description changes.
