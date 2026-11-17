# ANSWER: genai/ai-c1 An MCP server for store associates

## Approach

I started from what an associate actually asks ("do we have this", "is this pickup ready", "hold one
for this customer"), not from the REST endpoints. Then I wrote one test per review finding: tool list
by scope, schema limits, data minimization, scoping, the two-step write and audit.

## Fix

- `find_product` validates limit 1-10, returns compact items, and adds `more_results` plus a hint.
- `store_stock` defaults to the associate's store, and an unknown SKU error points the model to
  `find_product`.
- `order_lookup` covers this store's pickup orders only and returns one not-found message for missing
  or foreign orders. The customer appears as first name and initial only.
- With `write_scope`, `prepare_hold` issues a single-use token that expires in 120 s, and
  `hold_item_for_customer` consumes it after re-checking stock. Without the scope neither tool is
  registered.
- The hours resource is added, and every call, failed ones included, is appended to `srv.audit`.

## Trade-offs / what I would do in production

- Streamable HTTP with OAuth. The store scope comes from the token, never from a constructor argument
  or a tool argument.
- Per-associate rate limits, and audit records in an append-only store.
- A 20-question tool-selection eval that runs whenever a description changes.
- The two-step write adds one round trip; for a write that touches inventory that is worth it.
