# fde/w1-c1 - Agent loop over the blueprint executor

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 1 (Wed: Messages API tool use, Thu: prompt caching); AI Integration area 2 (the agent loop)

## Scenario

Aldermoor Living runs the commerce-agents retail vertical, but its platform team wants a
thin, auditable loop of its own instead of the blueprint's runtime package: their SRE
review asked for "a loop we can read in one sitting". You are writing it. It must run the
blueprint's own `ShoppingToolExecutor` (so gates, fencing and provenance are unchanged),
keep the prompt cache warm (the static prefix is ~6k tokens on every call), and never send
the API a request it would reject.

Last week's prototype paged on-call twice: once with
`400 invalid_request_error: messages.3: tool_use ids were found without tool_result blocks
immediately after`, once because a model that kept searching ran 19 rounds on one turn.

## What you build

Edit `agent_loop/loop.py` (the TODOs): `build_request` and `run_turn`.
`agent_loop/fake_client.py` is given: a fake `AsyncAnthropic` that replays recorded
responses from `fixtures/*.json` as real `anthropic.types.Message` objects and validates each
request the way the Messages API does (400 on a malformed conversation). Do not change it.

## Acceptance criteria

- Request layout matches `commerce_common.prompt_assembly`: the static system text is the
  first system block with `cache_control: ephemeral`; the per-request context is a second
  system block without it; the last tool (only) carries `cache_control`. The caller's
  `tools` list and dicts are never modified, and tool order is preserved.
- The tools + static system bytes are identical on every call of every turn (the cache
  prefix); only the second system block varies.
- Every `tool_use` block in a response runs **concurrently** through `executor.execute`,
  and is answered by a `tool_result` with the same id, **in tool_use order**, in one user
  message that holds only tool results.
- `is_error` comes from `ToolOutcome.is_error`. A held outcome (provenance gate, `blocked`
  set) is a normal result, not an error.
- The loop stops on any stop reason other than `tool_use` (`end_turn`, `max_tokens`) and
  returns the response's text as `final_text`.
- After `max_iterations` tool rounds, one final call with `tool_choice: {"type": "none"}`
  closes the turn; the tools stay in that request.
- `usage` sums `input_tokens`, `output_tokens`, `cache_read_input_tokens` and
  `cache_creation_input_tokens` across the turn's calls; `events` collects the outcomes'
  host events in tool_use order; the caller's `messages` list is not mutated.

## How to run

```bash
make setup     # builds/reuses the shared venv fde/.venv (blueprint installed editable)
make test      # visible tests (layout + happy path)
# from workbooks/: /grade fde/w1-c1    (adds hidden tests for every criterion above)
make clean
```

No test calls the real API. If you want to see the real thing, point `run_turn` at
`anthropic.AsyncAnthropic()` in a scratch script of your own with your key; the grader
never does.

Read first: `commerce-common/commerce_common/prompt_assembly.py`,
`commerce-common/commerce_common/turn.py` (`StreamedRound`, `log_model_call`),
`shopping-agent/core/shopping_agent/executor.py`, and the fixtures.

## What to submit

`agent_loop/loop.py` and a filled-in `ANSWER.md`. Explain why the forced final round keeps
the tools, and what you would add before production (streaming, retries on 429/529,
rolling message breakpoint, per-call logging).
