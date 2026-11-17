# Rubric: awsfde/w2-t1 "Order tool unavailable" after the Gateway release
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the Gateway passes the tool name as `<targetName>___<toolName>` in `context.client_context.custom["bedrockAgentCoreToolName"]`; the handler takes `split("_")[-1]`, which happens to work for the single-word `search` but turns `lookup_order` into `order` and `get_invoice_total` into `total`, so the function raises `Unknown tool` and the Gateway returns a tool error the agent paraphrases as "unavailable". Partial (10-15): "tool name parsing is wrong" without why search works or the delimiter. Zero: blames auth, IAM or the model. |
| 3 | Evidence | 20 | Full: quotes the Lambda log (`"tool": "order"`, `[ERROR] ValueError: Unknown tool: order`), the gateway log showing `tools/list` 200 with the prefixed names and `tools/call` reaching the function (`lambdaInvoke: FunctionError`, not an invoke failure), and the code line. Partial: one source. |
| 4 | Red herrings handled | 5 | Explains why the JWT authorizer (401s only 09:14-09:15 from the old SigV4 build, stopped when the agent build with OAuth rolled out; later calls are 200 and invoke the function) and the new role (search invokes the same function successfully) are not the cause; notes the rename only changed the prefix. |
| 5 | Fix quality | 10 | Split once on `___` (partition or index as in the Gateway docs), no-prefix fallback, schema validation, error objects with codes, no unhandled exceptions; tools.py behavior unchanged. |
| 6 | Prevention / production | 10 | Concrete: a contract test that builds Gateway-shaped contexts for every tool in tools.json, Lambda Errors alarm per target, a deploy smoke test calling each tool through the gateway, staging with the production target name. Partial: generic. |
Total: 100
