# Reference: fde/w3-c1 AgentTrustMixin

The full reference is `.grading/solution/trust_mixin/mixin.py`. The shape:

```python
async def _assess(self, hook, policy, session, **fields) -> Decision | None:
    request = RiskRequest(hook=hook, session_digest=digest(session.session_id),
                          user_digest=digest(session.user_id), **fields)
    started = time.monotonic(); result = None; error = None
    try:
        async with asyncio.timeout(policy.timeout_s):
            result = await self._risk.assess(request)
    except TimeoutError:
        error = "TimeoutError"
    except Exception as exc:          # NOT BaseException: CancelledError must propagate
        error = type(exc).__name__
    ...log exactly one DecisionRecord (sink failures swallowed)...
    return result.decision if result else None
```

- Cart hooks: `None` + closed -> `TrustUnavailable`; DENY -> `TrustDenied`; ALLOW/REVIEW ->
  `super()`. `TrustAwareExecutor.domain_error` maps `TrustDenied` to
  `ToolOutcome.held("trust", CART_DENIED_TEXT)` and `TrustUnavailable` to
  `ToolOutcome.error(CART_UNAVAILABLE_TEXT)`, then defers to `super().domain_error`.
- Checkout: `checkout_handoff` is the only checkout hook a backend has (the `checkout`
  presentation tool's enrich step calls it after the model's call). `run_presentation`
  turns `PresentationRefused(text, gate)` into a held result and `PresentationRefused(text)`
  into an error result, so deny/review/fail-closed map without touching the executor.
- `update_cart_item` reads the line through `self.get_cart` (not overridden, so never
  assessed) and assesses the delta only when it grows.

## Why these seams

- `domain_error` is the blueprint's sanctioned mapping from backend exceptions to tool
  results, and it runs on all three paths because the Messages API runtime, the SDK toolset
  and the MCP server all call `executor.execute`. Raising `Unavailable` instead would reuse
  "Nothing was added: ..." wording meant for stock, and leaks the wrong reason to the model.
- A held result (status `blocked`) tells the model "a gate decided" rather than "the system
  is down", so it does not retry; an error result for fail-closed tells it the tool is
  temporarily unavailable.
- Nothing in the prompt or the tool list changes, so `cache_read_input_tokens` is unaffected.

## Production trade-offs worth hearing

- `gated_add_to_cart` holds the per-session cart lock across `backend.add_to_cart`, so the
  risk call runs under the lock: parallel adds in one turn serialize behind the risk API.
  Acceptable at 150 ms; the alternative (assess outside the lock) needs the gate rewritten
  or a re-check after acquiring.
- Fail-open on cart is abusable during a brownout only if checkout also fails open; the
  matrix keeps the money step closed. Add a circuit breaker so a dead risk API costs ~0 ms,
  not 150 ms, per write.
- No retries inside a 150 ms budget; one attempt, then policy.
- Decision ids should be logged and sent back as an outcome report (chargeback feedback).
- Review at cart is deferred, not dropped: a production version would remember it and step
  up at checkout even if checkout's own decision is allow.
