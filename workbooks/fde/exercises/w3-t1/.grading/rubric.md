# Rubric: fde/w3-t1 Checkout silently allowed during a risk-API brownout
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified precisely | 25 | Full: env values are strings, `bool("false")` is True in `_env_flag` (`northwind_trust/policy.py`), activated by 1.4.0 adding `TRUST_CHECKOUT_FAIL_OPEN=false` where the code default had applied before; notes the cart flag masked it. Partial (10): "config parsing bug" without the mechanism or without the release link. Zero: blames the brownout, the breaker change, or the dependency bumps. |
| 3 | Evidence | 20 | Full: concrete commands and excerpts, e.g. checkout fail outcomes by version/error/policy across the two brownout logs (148 fail_closed in 1.3.2 vs 376 fail_open in 1.4.0, `"policy":"open"`), the diff hunk, and a `make replay` before/after. Partial: one source only. Zero: assertions without evidence. |
| 4 | Red herrings ruled out | 10 | Explains why the brownout (trigger, not cause), breaker 10 -> 5 (changes timing, not policy) and anthropic/httpx bumps are not the cause, with evidence. |
| 5 | Fix quality | 10 | Explicit parsing, case/whitespace tolerant, garbage raises at startup with the variable named, defaults kept for unset; does not just delete the env line or hard-code closed. |
| 6 | Production follow-up | 5 | Concrete: typed settings, release-time contract test on the real env file, alert on checkout fail_open, customer/fraud-ops remediation for the window. |
Total: 100
