# ms/ai-c1 answer (model)

## Approach
Rewrote the tools as an API for a model: precise names, descriptions with when/returns/limits,
strict schemas, and place_order taking only a quote_id. The loop executes tool_use blocks in
order, answers every call (even ones it refuses to execute), sums usage and stops on end_turn,
max_tokens or the turn limit.

## Fix
`make demo` on the injection fixture: get_quote(500) -> invalid_input (quantity max 100);
place_order(Q-9999) -> policy_violation (not issued in this session); get_quote(100) succeeds;
place_order(Q-1001) -> policy_violation (not confirmed by the technician). Orders placed: [].
The confirmation is set only by the app via Session.confirm, so no model output can satisfy it.

## Trade-offs / what I would do in production
In Copilot Studio the same policy belongs in the agent flow / API behind the tool, with a
Question node or adaptive card for confirmation; in Foundry the function-tool executor enforces
it. Still needed: idempotency on order submission, per-user quantity and value limits, audit
log of tool calls (without PII), Prompt Shields on retrieved content, and telemetry on
policy_violation rates as an attack signal.
