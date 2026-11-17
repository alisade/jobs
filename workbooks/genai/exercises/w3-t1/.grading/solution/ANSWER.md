# ANSWER: genai/w3-t1 The assistant's model bill went up 9x overnight

## Approach

I read `traffic.txt` first. Sessions rose 30 percent but provider requests per question went from 1.00
to 3.56, so the multiplier is per question, not traffic. `make report` grouped the usage export by
fingerprint, and the gateway log and `make demo` confirmed the mechanism.

## Root cause

The gateway's fixed 10 s read timeout is shorter than a comparison answer takes to generate after
release 2026.11.10 (max_tokens 512 to 2048). The provider finishes and bills every request the
gateway gave up on, and the gateway retries timeouts at once: 4 times on the primary and 4 on the
fallback.
- `make report`: 145 billed rows for 40 conversations. For example `60e3fce07029 billed 8x $0.159
  models=fallback,primary output_tokens=1977 duration_s=14.44`, which means 14.4 s against a 10 s timeout.
- `gateway.log`: `conv=c-8f21aa model=primary attempt=1..4 read timeout after 10.0s`, the same for the
  fallback, then `500 GatewayError: all models failed (70.1s)`. Failed attempts log no tokens or cost,
  so our own logs hid the spend.
- `make demo`: 145 billed generations for 40 questions, $2.41 billed against $0.11 delivered, and 15 of
  40 questions failed.

The marketing email is not the cause. It added 30 percent more sessions, which explains 1.3x of the
cost, not 9x.

## Fix

- Timeout is now `5 s + max_tokens / 100`.
- 400 is raised at once.
- 429/529 retry with equal-jitter exponential backoff, waiting at least retry-after.
- A timeout moves to the fallback and is never repeated on the same model.
- Primary and fallback share 3 attempts.
- A per-request cost cap counts the worst-case cost of timed-out attempts.
- Every attempt is logged with outcome, tokens, cost and `discarded`.

After the fix, `make demo` shows 40 calls for 40 questions, $0.57 billed equal to $0.57 delivered, and
no failures. All tests pass.

## Trade-offs / what I would do in production

- Stream long answers with an idle timeout instead of a long total timeout.
- Keep one retry layer, and check that SDK default retries are off.
- Alert on billed vs delivered tokens and on requests per question.
- Put per-request cost in traces for finance.
- The cost cap may fail a legitimately expensive question. Tune it from the distribution of real
  request costs.
