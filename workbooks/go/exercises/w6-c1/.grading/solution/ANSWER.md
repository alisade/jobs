# go/w6-c1 ANSWER (model)

## Approach

Read `fake_test.go` to see the exact wire format, then wrote the loop as a state machine
on `stop_reason`. Built tests turn by turn: single tool, parallel tools (a barrier proves
they run concurrently), every is_error path, then budget and cancellation.

## Fix

- `New`: defaults via `cmp.Or`; registry validation; one `anthropic.ToolParam` per tool.
- `Run`: budget check before each call; `msg.ToParam()` appended every turn; explicit
  switch on stop reasons; summed usage; partial `Result` returned with every error.
- `runTools`: errgroup with `SetLimit(MaxParallel)`, results written by index, per-call
  timeout, recover inside the goroutine; one user message of tool_result blocks.
- Unknown tool, invalid input, handler error, panic, timeout -> `is_error: true`.

## Trade-offs / what I would do in production

- Add a token budget and wall-clock deadline per run, not just a turn cap.
- Cache the static prefix (system + tools) with a `cache_control` breakpoint.
- Keep SDK retries on (off only in tests); add OTel spans per turn and per tool.
- Run on Bedrock via Pod Identity; tools stay read-only, mutations need server-side authz.
