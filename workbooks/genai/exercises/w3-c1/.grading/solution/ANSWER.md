# ANSWER: genai/w3-c1 Assistant agent endpoint with a confirm-before-write tool

## Approach

I listed the security review's findings as rules and put each one in code the model cannot influence:
the tool layer (identity and ownership), the loop (read and write split, limits) and the confirm
endpoint (owner, single use, TTL). Each rule has a test that scripts a misbehaving model.

## Fix

- The loop runs read tools. `start_return` only creates a `PendingAction` with whitelisted args and a
  5-minute expiry, and the model is told it is pending. Only one proposal is allowed per turn.
- `/actions/{id}/confirm` returns 404 for unknown actions and other users' actions, 409 for a used one
  and 410 for an expired one, and executes at most once.
- Order lookups check ownership. "Not yours" and "missing" share one message.
- `MAX_TURNS` returns `GAVE_UP` with `truncated`. Errors and unknown tools come back as `is_error`
  results. Output is capped. Every call is audited with its decision. Conversations are bound to the
  user who started them.

## Trade-offs / what I would do in production

- Pending actions go in Redis with a TTL so any replica can confirm. The confirm screen shows the
  server's summary.
- Downstream calls carry the customer's token, so the orders service enforces ownership too (defence
  in depth).
- Audit records go to an append-only store.
- I would rate-limit proposals.
- The cost is one extra click per return, which is the correct trade-off for a write that sends money
  back.
