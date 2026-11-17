# awsfde/w1-c1 - Converse tool-use loop with a guardrail, tenant-safe tools and cost logging

**Type:** coding | **Estimate:** 2 hours | **Study plan:** Week 1 (Mon: Converse API; Tue: tool use; Wed: Guardrails; Thu: tokens, cost and invocation logging)

## Scenario

Tidewater Analytics (fictional) sells Tidewater Ask, a multi-tenant "ask your data" assistant for
freight and supply-chain customers. You are the forward deployed engineer on the first production
cut of its support assistant. The customer, Acme Foods, wants to ask "where is SH-10001?" and
"open a ticket, the pallet arrived damaged" in plain language.

The prototype was a notebook that called `InvokeModel` with a hand-built prompt. You are moving it
to the Bedrock **Converse API** with real tool use, a Bedrock **guardrail** attached, and token and
cost accounting the customer's FinOps team asked for before go-live. The security review added one
hard rule: a tool must take the tenant from the verified caller context, never from anything the
model produces.

## What you have

| Path | What it is |
|---|---|
| `config.json` | model id (a US cross-Region inference profile), guardrail id and version, limits, an illustrative price table |
| `ask_agent/context.py` | `CallerContext`: tenant, user and request id from the verified JWT (done) |
| `ask_agent/tools.py` | the two tool specs and their DynamoDB handlers (done; read them) |
| `ask_agent/loop.py` | `build_request()` and `run_turn()` - **your work** |
| `ask_agent/costs.py` | `Usage.add()` and `estimate_cost_usd()` - **your work** |
| `tests/` | visible tests: a moto DynamoDB table and a real `bedrock-runtime` client with a botocore `Stubber` |

The Stubber replays recorded Converse responses, and botocore validates every request you send
against the real Converse API model, so a malformed request fails the test the way it would fail
with a `ValidationException` in AWS. Nothing calls AWS.

## Your task

1. `build_request(config, messages)`: the keyword arguments for `converse()`: `modelId`, the system
   prompt as a `system` block, `messages`, `toolConfig` with both tool specs (in that order),
   `inferenceConfig.maxTokens`, and `guardrailConfig` with the id, version and `trace: "enabled"`.
2. `run_turn(client, table, ctx, question, config)` runs the loop:
   - Start with one user message holding the question.
   - `stopReason == "tool_use"`: append the assistant message exactly as returned, run **every**
     `toolUse` block, and send all results back in **one** user message, in the same order.
     Success is `{"toolResult": {"toolUseId", "content": [{"json": ...}], "status": "success"}}`.
   - A failure the model can act on is a `toolResult` with `status: "error"` and a short text,
     never an exception: unknown tool, input that fails the tool's JSON schema (validate with
     `jsonschema` before the handler runs), `ToolError` from a handler, or an unexpected handler
     exception (generic message, no internals).
   - Handlers always get the verified `ctx`. A `tenant_id` in the model's tool input is never
     used; log it as an `ignored_tenant_arg` event.
   - `"guardrail_intervened"`: outcome `blocked`, the answer is the guardrail's message text, record
     the trace's `actionReason` in `guardrail_action`, run no tools.
   - `"max_tokens"`: outcome `truncated`. `"end_turn"`: outcome `answered`.
   - At most `max_tool_rounds` rounds of tool execution; if the model still asks for tools after
     that, stop with outcome `max_rounds` (so at most `max_tool_rounds + 1` Converse calls).
   - Record every tool call in `tool_calls` as `{"name", "status", "toolUseId"}`.
3. `Usage.add()` sums input, output, cache read and cache write tokens and latency across calls;
   `estimate_cost_usd()` prices each token type from `config.json` and raises `KeyError` for a
   model that has no price.
4. Log one JSON line per model call on logger `tidewater.ask` with at least `request_id`,
   `tenant_id`, `round`, `stop_reason`, `input_tokens`, `output_tokens`, `latency_ms`.
5. Fill in `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- Every request passes botocore validation and carries the tools, guardrail and limits.
- Parallel tool calls come back in one message, in order, with matching `toolUseId`s.
- Errors become `status: "error"` results; invalid input never reaches a handler.
- A forged `tenant_id` tool argument cannot read or write another tenant's items.
- Guardrail, truncation and round-limit outcomes are correct; usage and cost add up across rounds.
- One JSON log line per model call; a `ValidationException` from Bedrock is not swallowed.
- `ANSWER.md` explains your choices and what you would add for production.

## How to run

```bash
make setup     # builds the shared venv awsfde/.venv on first use
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade awsfde/w1-c1
make clean
```

Optional, outside the grader: point the same code at a real account with a real guardrail and a
model you have access to, and compare the logged tokens with the `usage` block and CloudWatch
`InputTokenCount`/`OutputTokenCount` metrics.
