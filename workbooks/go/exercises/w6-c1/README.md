# go/w6-c1 Incident-triage agent loop with anthropic-sdk-go

**Type:** coding | **Estimate:** 3 hours | **Week 6:** Mon, Anthropic Go SDK: tool use and the agent loop

## Scenario

Kestrel's platform team wants a triage agent that runs in-cluster and answers "why is
checkout paging?" by calling read-only platform tools (pod events, PromQL) before giving a
root-cause hypothesis. The prototype was a Python notebook that ran tools one at a time,
crashed when the model asked for a tool that did not exist, and once looped 40 turns on a
flapping metric and burned a day of budget. You are writing the production loop in Go
with `github.com/anthropics/anthropic-sdk-go`.

## Task

Implement `New` and `Agent.Run` in `agent/agent.go`. Keep the exported names and
signatures; the hidden tests use them. `cmd/triage` is an optional live demo, not graded.

## Requirements

1. **Registry.** `New` rejects empty names, nil handlers and duplicate names. Each tool is
   sent on every request as a custom tool with `name`, `description` and an
   `input_schema` of `type: object` with the tool's `properties` and `required`, in
   registration order.
2. **Defaults.** Model `anthropic.ModelClaudeSonnet5_5`, `MaxTokens` 2048, `MaxTurns` 8,
   `MaxParallel` 4, `ToolTimeout` 20s. `System` is sent only when non-empty.
3. **Loop.** One turn is one `Messages.New` call with the full transcript. Append the
   assistant message (`msg.ToParam()`) every turn.
4. **Stop reasons.** `end_turn` / `stop_sequence`: return the text blocks joined with
   `"\n"`. `max_tokens`: return the partial text and `ErrMaxTokens`. `refusal`: `ErrRefusal`.
   `tool_use`: run the tools and continue. Anything else: an error.
5. **Parallel tool calls.** All `tool_use` blocks of a turn run concurrently, at most
   `MaxParallel` at a time, and their results go back in **one** user message with one
   `tool_result` per `tool_use`, in the same order, with matching `tool_use_id`.
6. **Recoverable tool errors are data.** Each of these becomes a `tool_result` with
   `is_error: true` and a message the model can act on, and the loop continues:
   unknown tool (list the available tools), input that is not a JSON object or is missing
   a required field (name it; do not call the handler), handler error (include its text),
   handler panic, handler exceeding `ToolTimeout`.
7. **Budget.** If the model still wants tools after `MaxTurns` calls, return
   `*MaxTurnsError` (`errors.As`) with `Turns` set. Never make call `MaxTurns+1`.
8. **Failure paths.** API errors are returned wrapped (`errors.As(err, **anthropic.Error)`
   works). Context cancellation, including during tool execution, returns an error wrapping
   `context.Canceled` and makes no further API calls.
9. **Accounting.** `Result` carries summed input/output tokens, `Turns`, `ToolCalls`, the
   final `StopReason` and the full transcript, also when an error is returned.
10. **Concurrency safety.** One `*Agent` can serve concurrent `Run` calls; transcripts
    must not leak between runs. Tests run with `-race`.

## Acceptance criteria

- `make test` passes with `-race`; `go vet` is clean.
- Hidden tests (fake Messages API over `httptest`) cover request shape, defaults,
  parallelism and ordering, the concurrency bound, every is_error path, the turn budget,
  stop reasons, API errors, cancellation, usage and concurrent runs.
- No test or grading step calls the real API.

## How to run

```
make setup   # modules + build
make test    # visible test against agent/fake_test.go (scripted Messages API)
make live    # OPTIONAL, real API, needs ANTHROPIC_API_KEY, costs money; never graded
```

Read `agent/fake_test.go`: it shows the exact JSON the fake returns and records.

## What to submit

`agent/agent.go` and `ANSWER.md`, then `/grade go/w6-c1` from the workbooks root.

## Study-guide links

- anthropics/anthropic-sdk-go: https://github.com/anthropics/anthropic-sdk-go
- Claude docs, tool use: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- Building effective agents: https://www.anthropic.com/engineering/building-effective-agents
- errgroup: https://pkg.go.dev/golang.org/x/sync/errgroup
