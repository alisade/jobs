# Reference: fde/w3-t1

**Root cause:** `northwind_trust/policy.py:_env_flag` did `bool(env.get(name, default))`.
Environment values are strings and any non-empty string is truthy, so
`TRUST_CHECKOUT_FAIL_OPEN=false` meant fail-OPEN. Release 1.4.0 (SRE-412) added that line
to `deploy/trust.env` to "make defaults explicit"; before it, the variable was unset and the
real `False` default applied. The cart flag (`true`) was right by accident.

**Evidence the learner should find:**
- Checkout failures by version: 1.3.2 brownout -> 148 `fail_closed` (TimeoutError,
  BreakerOpen); 1.4.0 brownout -> 376 `fail_open`, every line `"policy":"open"`.
- The diff hunk `+TRUST_CHECKOUT_FAIL_OPEN=false`.
- `make replay` with the deployed env: checkout renders a card (`events=['ui']`).

**Red herrings:** the brownout (trigger), breaker threshold 10 -> 5 (timing only; BreakerOpen
follows the same policy), anthropic/httpx bumps (timeouts were enforced at the budget).

**Fix:** `.grading/solution/northwind_trust/policy.py`: explicit parser accepting
true/false/1/0/yes/no/on/off (trimmed, case-insensitive), raising `ValueError` naming the
variable on anything else; unset keeps defaults. `build_backend` loads the policy at
startup, so a typo stops the pod rather than choosing a fail mode.

**Production:** typed settings model, release-pipeline test against the real env file,
effective policy in startup logs and health endpoint, alert on `checkout fail_open`,
remediation for the incident window.
