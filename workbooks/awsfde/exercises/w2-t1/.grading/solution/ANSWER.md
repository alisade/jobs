# ANSWER: awsfde/w2-t1 "Order tool unavailable" after the Gateway release

## Approach

Checked whether calls reach the function at all (gateway log), then what the function received and
did (Lambda log), then the dispatcher code. Auth last, because tools/list and search succeed after
09:16.

## Root cause

`tool_name_from_context` returns `full.split("_")[-1]`. The Gateway sends
`bedrockAgentCoreToolName = "<targetName>___<toolName>"`, so `tw_orders___lookup_order` becomes
`order`:

    {"event": "tool_call", "tool": "order", "gateway": "tw-ask-acme-gw-k3j9x2m4pq", ...}
    [ERROR] ValueError: Unknown tool: order RequestId: ... (function error, Unhandled)

The gateway log shows the call reached the function: `"name": "tw_orders___lookup_order", "status":
200, "lambdaInvoke": "FunctionError"`. `search` works only because it is one word.

Not the cause: the CUSTOM_JWT authorizer (401s only from the old SigV4 agent build at 09:14-09:15,
then 200s), the new role (search invokes the same function), the target rename (prefix only).

## Fix

Partition on "___" with a no-prefix fallback; jsonschema validation against tools.json; error
objects UNKNOWN_TOOL / INVALID_INPUT / NOT_FOUND. `make replay`: 11 tool calls, 1 isError (PO-99999).

## Trade-offs / what I would do in production

Contract test with Gateway-shaped contexts for every tool; Lambda Errors alarm per target; post-deploy
smoke test through the gateway; same target name in staging and prod.
