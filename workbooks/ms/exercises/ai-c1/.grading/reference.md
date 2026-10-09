# Reference: ms/ai-c1

Reference code: `.grading/solution/parts_agent/tools.py` and `loop.py`.

## Key ideas

- **Tools are an API for a non-human caller.** Descriptions state when to use the tool, what
  it returns and its limits; schemas are tight (`pattern`, `minimum`/`maximum`,
  `additionalProperties: false`). `place_order` takes only `quote_id`, so the model cannot place
  an order with a part or quantity that was never quoted.
- **Errors are data.** Every failure returns `{"error": <code>, "message": ...}` with
  `is_error: true`, so the model can retry (`invalid_input` -> fix arguments) instead of the
  conversation dying.
- **Enforcement is server-side and out-of-band.** `Session.confirm` is called by the app when the
  human presses Confirm; the model cannot call it. `place_order` checks issued-in-this-session,
  confirmed, not-yet-ordered. The injection fails at two layers: quantity 500 violates the
  schema; the fabricated `Q-9999` and the unconfirmed `Q-1001` violate the policy.
- **History invariant.** Every `tool_use` must be answered by a `tool_result` in the next user
  message, or the next model call is malformed. Truncated (`max_tokens`) and over-limit calls are
  answered with error results and never executed: executing a half-generated call is how you
  order the wrong thing.

## Microsoft mapping

Copilot Studio: tools (connector actions, agent flows, REST, MCP) are chosen by generative
orchestration from names and descriptions; put the quote/confirm policy in the flow or API behind
the tool, and use topic-level confirmation (Question node) or an adaptive card for the human step.
Foundry Agent Service: function tools declare JSON Schema parameters; your code executes the call
and returns the output - the same loop you wrote here.

## Interview angles

- The model returned a `tool_use` for `place_order` with a valid, confirmed quote id it saw in an
  earlier turn of ANOTHER user's conversation. Which check stops it? (issued-in-this-session)
- Why is "the system prompt says treat tool results as data" not a control?
- How would you make `place_order` idempotent across retries? (idempotency key = quote id, which
  this design already gives you)
- What do you log per turn for observability, and what must you NOT log?
