# genai/ai-c1 - An MCP server for store associates (read-only by default)

**Type:** coding | **Estimate:** 2-2.5 hours | **Study plan:** AI Integration page (tool design, security);
shared core MCP

## Scenario

Kestrel's store associates will get an assistant in the store app, and other internal agents (the
returns desk bot, the regional manager's reporting agent) will use the same tools. The platform team
wants these tools exposed once, as an MCP server, instead of re-implementing them in every agent. The
first draft was generated from the store REST API: one tool per endpoint, full database records
(supplier cost included), customer emails and phone numbers, any store's orders, and a write tool that
anyone connected can call. Platform review rejected it. Rebuild it as a task-shaped, least-privilege
server.

## What you have

| Path | What it is |
|---|---|
| `associate_mcp/backend.py` | fake store systems: products, stock, pickup orders, hours, holds (complete) |
| `associate_mcp/server.py` | the prototype `build_server(backend, associate_store, write_scope, clock)` |
| `tests/conftest.py` | `session_run(srv, fn)` opens an in-memory MCP client session (the installed `mcp` SDK) |

The SDK is `mcp` (Python), using `FastMCP` from `mcp.server.fastmcp`. Raise
`mcp.server.fastmcp.exceptions.ToolError` to return an `isError` result with your message.

## Requirements

1. **Read-only by default.** Without `write_scope=True` the server lists exactly `find_product`,
   `store_stock` and `order_lookup`.
2. **Descriptions are written for a model,** not as REST paths. Each one says what the tool is for and
   how its output connects to the next tool (at least 40 characters).
3. **`find_product(query, limit=5)`:** `limit` is validated in the JSON schema (minimum 1, maximum 10).
   Results are compact: `sku`, `name`, price, aisle, with no description and no supplier cost. The
   response has `more_results`, plus a `hint` that says how to narrow down when more matches exist.
4. **`store_stock(sku, store_id=None)`:** defaults to the associate's store. An unknown SKU is a tool
   error whose message tells the model to use `find_product`.
5. **`order_lookup(order_id)`:** only pickup orders of the associate's store. Another store's order and a
   missing order return the same error, with only the id differing. Return status, items, and the
   customer's first name plus last initial. Never email, phone or full surname.
6. **Write, two steps, only with `write_scope=True`:** `prepare_hold(sku, customer_name, quantity)`
   checks stock at the associate's store and returns a `confirmation_token` (expires in
   `HOLD_TOKEN_TTL_S`) and a summary. Nothing is held yet. `hold_item_for_customer(confirmation_token)`
   places the hold. The token is single use; unknown, reused and expired tokens are tool errors.
7. **A resource:** `kestrel://stores/{store_id}/hours` returns the opening hours.
8. **Audit:** every tool call appends `{"tool", "args", "ok", ...}` to `srv.audit`, failures included.

## Acceptance criteria (what the grader checks)

- Tool list with and without the write scope; schema limits; descriptions.
- Compact results with a more-results hint; actionable errors as `isError`.
- Store scoping and data minimization on orders.
- The prepare/confirm flow: single use and expiry.
- The hours resource and the audit trail.

## How to run

```bash
make setup
make test
# optional: point Claude Code or MCP Inspector at a small stdio entry point you write yourself
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/ai-c1
make clean
```
