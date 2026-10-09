# ANSWER: fde/w3-t1 Checkout allowed during a risk-API brownout

## Approach

Started from the page: chargebacks with an empty `risk_decision_id`, all in the Halyard
brownout window, none in the previous brownout. So the question is not "why was Halyard
slow" but "what did our client do differently with the same failure in 1.4.0".

Compared the two decision logs for checkout failures:

```
$ jq -r 'select(.hook=="checkout" and (.outcome|startswith("fail"))) | [.version,.outcome,.error,(.policy//"-")] | @tsv' decisions-2026-09-28.jsonl | sort | uniq -c
  54 1.3.2  fail_closed  BreakerOpen   -
  94 1.3.2  fail_closed  TimeoutError  -
$ (same over decisions-2026-10-06.jsonl)
 254 1.4.0  fail_open    BreakerOpen   open
 122 1.4.0  fail_open    TimeoutError  open
```

Same failure types (timeouts, then breaker-open), opposite outcome. The 1.4.0 log line
even records the policy in force for checkout: `"policy":"open"`. So the process was
running with checkout fail-open, while `deploy/trust.env` says `TRUST_CHECKOUT_FAIL_OPEN=false`.

`make replay` reproduced it locally with the deployed file: checkout returns
`is_error=False events=['ui']` and logs `fail_open ... "policy":"open"`.

Ruled out:
- The brownout itself: it is the trigger, and the 09-28 brownout failed closed.
- The breaker change (10 -> 5): it changes how soon `BreakerOpen` appears, not what a
  failure means; both `TimeoutError` and `BreakerOpen` follow the hook policy, and both
  went open in 1.4.0.
- The anthropic/httpx bumps: timeouts were enforced (latency_ms 400-404, the budget), and
  the risk client path does not use the Anthropic SDK.

## Root cause

`northwind_trust/policy.py:_env_flag` returned `bool(env.get(name, default))`. Environment
values are strings, and every non-empty string is truthy, so `bool("false") is True`.

1.3.2 never set `TRUST_CHECKOUT_FAIL_OPEN`; the code default `False` (a real bool) applied
and checkout failed closed. Release 1.4.0 (SRE-412, "make every trust default explicit")
added `TRUST_CHECKOUT_FAIL_OPEN=false` to `deploy/trust.env`. That string turned checkout
into fail-open. The cart flag (`=true`) had always "worked" because `"true"` is also truthy,
which hid the bug. It is still live: any brownout today allows checkout without a decision.

## Fix

- `_env_flag` parses explicitly: trimmed, case-insensitive `true/false/1/0/yes/no/on/off`;
  unset keeps the default; anything else raises `ValueError` naming the variable, so
  `build_backend` (called at startup) refuses to start on a typo instead of picking a fail
  mode silently.
- Verified: `make test` and the hidden suite pass; `make replay` now shows checkout
  `is_error=True events=[]` with `fail_closed ... "policy":"closed"`, cart still writes.

## Trade-offs / what I would do in production

- Parse all config through a typed settings model (pydantic-settings) instead of hand
  helpers; add a startup log line and a `/healthz` field with the effective policy, and an
  alert on any `hook=checkout outcome=fail_open` when the policy is meant to be closed.
- A contract test that loads the real `trust.env` and asserts the effective policy, run in
  the release pipeline (this would have failed 1.4.0).
- Fail-closed checkout costs conversions during brownouts; tell the business that number
  and offer a queued "verify in app" path rather than reopening fail-open.
- Notify fraud-ops of the affected window (decision log gives the session digests) and
  backfill outcome reports to Halyard for the 37 chargebacks.
