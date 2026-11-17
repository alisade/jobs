# Reference: awsfde/w2-t1

## Root cause

AgentCore Gateway invokes a Lambda target with `event` = the tool arguments and the tool name in
`context.client_context.custom["bedrockAgentCoreToolName"]`, formatted `<targetName>___<toolName>`
(three underscores; the Gateway docs' boilerplate strips the prefix with `index("___")`). The handler
used `full.split("_")[-1]`:

- `tw_orders___search` -> `search` (works by accident: single-word tool)
- `tw_orders___lookup_order` -> `order` -> `ValueError: Unknown tool: order`
- `tw_orders___get_invoice_total` -> `total`

The function error comes back to the agent as an MCP tool result with `isError`, and the model tells
the user the tool is "unavailable". Unit tests in the release called `tools.lookup_order` directly, so
the dispatcher was never tested with Gateway-shaped names.

## Red herrings

- **CUSTOM_JWT authorizer.** The 401s are 09:14:52-09:15:40 from the agent build that still signed
  with SigV4; they stop when the OAuth build rolls out at 09:16. Every later call is 200 at the gateway
  and invokes the function (`lambdaInvoke: FunctionError`, not an invoke or auth failure).
- **New execution role.** `search` invokes the same function successfully with the same role.
- **Target rename** `orders` -> `tw_orders`: only changed the prefix; it would have broken any code
  that matched on the full name, but not this one.

## Fix

`full.partition("___")`, fall back to the whole name when there is no prefix, validate the event
against the tool's `inputSchema`, and return `{"error": {"code", "message"}}` for UNKNOWN_TOOL,
INVALID_INPUT and NOT_FOUND so the agent can recover or explain. See `.grading/solution/`.

## Prevention

A contract test that, for every tool in `tools.json`, builds a context with
`<production target name>___<tool>` and calls the handler; a Lambda `Errors` alarm on the target; a
post-deploy smoke test that calls each tool through the gateway with a test identity.
