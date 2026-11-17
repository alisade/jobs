# Reference: genai/w3-t1

## Root cause
Release 2026.11.10 raised `max_tokens` from 512 to 2048 and asked for side-by-side comparisons.
A comparison of about 1,900 tokens takes 0.6 + 0.007 x 1900, about 14 s, to generate. The gateway's
read timeout has been a fixed 10 s since August. The client gives up at 10 s, but the provider keeps
generating and bills the full answer. The gateway catches every `ProviderError`, timeouts included, and
retries at once: 4 attempts on the primary, then 4 more on the fallback. Each attempt times out in
the same way, so a single comparison question bills 8 full generations and the customer still gets
"something went wrong" after about 70 s. Short answers are unaffected, which is why spend rose
"only" 9x and not 8x across the board.

Evidence:
- `make report`: 40 conversations, 145 billed rows. The comparison fingerprints are billed 8x each, on
  both models, at about 14.4 s each.
- `gateway.log`: `attempt=1..4 read timeout after 10.0s` per model, then `500 GatewayError ... (70.1s)`.
  Only successful attempts log tokens and cost, which is why nobody saw the spend in the app's own logs.
- `traffic.txt`: questions per session flat at 2.9, provider requests per question from 1.00 to 3.56.

Red herring: the email increased sessions by about 30 percent. That accounts for 1.3x, not 9x.

## Fix (solution/assistant_gateway/gateway.py)
- `timeout_for(max_tokens) = 5 s + max_tokens / 100 tokens per second`, capped. Streaming with an idle
  timeout would be better still.
- `InvalidRequest`: raise at once. 429/529: equal-jitter exponential backoff, at least retry-after.
- `ProviderTimeout`: no repeat on the same model; move to the fallback.
- One loop over `max_attempts` (3) for primary and fallback together.
- Cost cap: add the worst-case cost of timed-out attempts (input + max_tokens) to `spent`; at the cap,
  raise `BudgetExceeded`.
- `attempt_log` gets one entry per call with outcome, tokens, cost and `discarded`.

## Prevention
- Alert on provider requests per question and on billed vs delivered output tokens.
- Retries live in one layer, with one budget. Count nested retries (SDK default retries count too).
- Stream long answers, so a slow generation is not a timeout.
- Before a prompt change ships, run a load test with production-length outputs.
- Put per-request cost in traces (OTel GenAI attributes) so finance can answer "what did this cost".
