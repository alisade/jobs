# Reference: fde/w1-c1 Agent loop

Full code: `.grading/solution/agent_loop/loop.py`. The shape:

```python
conversation = [*messages, {"role": "user", "content": user_text}]
while True:
    forced = tool_rounds >= max_iterations
    request = build_request(..., tool_choice={"type": "none"} if forced else None)
    response = await client.messages.create(**request)
    add usage (four fields); persist [b.model_dump(exclude_none=True) for b in response.content]
    uses = [b for b in response.content if b.type == "tool_use"]
    if response.stop_reason != "tool_use" or not uses or forced:
        return text blocks joined
    outcomes = await asyncio.gather(*(executor.execute(u.name, dict(u.input)) for u in uses))
    conversation.append({"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": u.id, "content": o.result_text, "is_error": o.is_error}
        for u, o in zip(uses, outcomes, strict=True)]})
    tool_rounds += 1
```

`build_request` copies each tool dict, marks only the last with `cache_control`, and sends
`system=[{static, cache_control}, {dynamic}]`, exactly as `build_system_blocks` and
`with_tool_cache_control` do in `commerce_common/prompt_assembly.py`.

## Points worth hearing in review

- Cache prefix order is tools, then system, then messages. Anything per-request before a
  breakpoint (a timestamp, a cart) changes the prefix hash and turns every call into a
  cache write. The blueprint puts the per-request block after the static block's marker.
- `gather` returns results in argument order regardless of completion order, so zipping
  back to `uses` is safe; building results in completion order (e.g. `as_completed`) is
  what produces the out-of-order bug, and missing a result is the classic 400.
- The forced round keeps `tools` and sets `tool_choice: none`: the API rejects tool_use
  history without tools, and dropping them would change the cached prefix anyway.
- A held outcome is information for the model ("resolve the id first"), not a failure;
  marking it `is_error` makes some models apologize and stop instead of following the hint.
- The executor never raises (`BaseToolExecutor.execute`), so gather needs no
  `return_exceptions`; with an arbitrary executor you would wrap each call so one failure
  still yields a tool_result.
- Production adds: streaming (`StreamedRound`), retries with jitter on 429/529, a rolling
  message breakpoint (`build_request_messages`), and one `log_model_call` line per call.
