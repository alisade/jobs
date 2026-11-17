# Reference: go/w6-c1 triage agent loop

Reference code: `.grading/solution/agent/agent.go`.

## Shape of the loop

```
messages = [user(prompt)]
for {
    if turns == MaxTurns -> *MaxTurnsError          (check BEFORE calling: never call MaxTurns+1)
    msg = Messages.New(model, max_tokens, system, tools, messages)
    turns++, usage += msg.Usage
    messages = append(messages, msg.ToParam())        (assistant turn, including tool_use blocks)
    switch stop_reason {
    end_turn, stop_sequence -> return text
    max_tokens -> return partial text, ErrMaxTokens
    refusal    -> ErrRefusal
    tool_use   -> results = runTools(tool_use blocks); messages = append(messages, user(results...))
    default    -> error
    }
}
```

## Points worth noticing

- **One user message with every tool_result, in tool_use order.** The API requires each
  `tool_use` id to be answered in the next user message. Writing results into
  `out[i]` (preallocated) keeps order without a mutex; appending from goroutines would race
  and reorder.
- **errgroup without failing the group.** Each goroutine returns nil: a tool failure is
  information for the model (`is_error: true`), not a reason to abort siblings.
  `SetLimit(MaxParallel)` bounds concurrency. After `Wait`, check the parent `ctx` to tell
  cancellation apart from tool failures.
- **Two error classes.** Tool-level (unknown tool, bad input, handler error, panic,
  timeout) -> `is_error` result and continue. Run-level (API error, cancellation, budget,
  max_tokens, refusal) -> returned to the caller, wrapped with `%w`.
- **Validate before executing.** The model can omit or null required fields; the handler
  must not see invalid input. Schema enforcement lives server-side (here), never in the
  prompt.
- **Panic recovery belongs inside the goroutine.** A panic in an errgroup goroutine kills
  the process; `recover` must be deferred in the function that runs the handler.
- **No per-run state on Agent.** The transcript is a local; the registry is read-only after
  `New`, so concurrent `Run` calls are safe.
- **Defaults with `cmp.Or`.** Zero-value config is usable.

## Production notes a strong answer mentions

- Cost and loop guards: max turns, max total tokens per run, wall-clock deadline.
- Prompt caching: system + tools are a stable prefix; put a `cache_control` breakpoint on
  the last tool or the system block and watch `cache_read_input_tokens`.
- Retries: the SDK retries 429/5xx/529 with backoff by default (`option.WithMaxRetries`);
  tests turn retries off to stay fast and deterministic.
- Streaming (`Messages.NewStreaming`) for long answers and early UI feedback.
- OTel: a span per turn (model, tokens, stop reason) and per tool call (GenAI semconv).
- Bedrock backend via the SDK's bedrock option and EKS Pod Identity, no static keys.
- Tools stay read-only; anything mutating needs server-side authorization and a human
  confirmation step, because tool results can carry prompt injection.
