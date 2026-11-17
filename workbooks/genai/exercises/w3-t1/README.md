# genai/w3-t1 - The assistant's model bill went up 9x overnight

**Type:** troubleshooting | **Estimate:** 1.5-2.5 hours | **Study plan:** Week 3 (rate limits, retries
with backoff, timeouts, fallback models, cost and latency budgets, logging tokens per call)

## Symptom

Finance opened a ticket: Kestrel Outfitters' shopping assistant spent $3,710 on the model provider in
one day against a $410 average, and comparison questions fail after a long wait. Marketing thinks it is
their holiday email. Read `evidence/PAGE.md` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/PAGE.md` | the finance ticket and the thread |
| `evidence/usage-export.csv` | provider usage export, one row per BILLED generation (40 conversations) |
| `evidence/gateway.log` | gateway log lines for the same morning |
| `evidence/traffic.txt` | daily sessions, questions, provider requests and spend |
| `evidence/release-notes.md` | what shipped on Nov 10 |
| `assistant_gateway/gateway.py` | the LLM gateway (retries, fallback, attempt log): this is what you fix |
| `assistant_gateway/provider.py`, `clock.py`, `pricing.py` | local provider stand-in, fake clock and price list: do not edit |
| `scripts/cost_report.py` | `make report`: groups the usage export by request fingerprint; extend it |
| `scripts/simulate.py` | `make demo`: replays 40 production-shaped questions through the gateway on a fake clock |

The fake provider behaves like the real one where it matters: generation takes 0.6 s plus 7 ms per
output token, a request the client gave up on is still generated and **billed**, 429 carries a
retry-after, 529 is overload, 400 means the request is bad. `Stall` simulates a provider that is slow
today.

## Your task

1. Find the root cause and prove it with the evidence. Quote rows of the usage export and lines of the
   gateway log. Explain the multiplier (how many billed generations one question can cost), why only
   comparison questions fail, and whether the marketing email explains it.
2. Fix `assistant_gateway/gateway.py`. Keep the class names and `answer(conversation_id, messages,
   max_tokens)`, and keep the config fields `primary`, `fallback`, `max_attempts` (3) and
   `max_cost_usd`. Requirements:
   - a normal long answer (up to `max_tokens`) completes in one billed call: size the timeout to the
     answer budget instead of a fixed 10 s;
   - 400 invalid requests are never retried and never sent to the fallback;
   - 429 and 529 are retried with exponential backoff and jitter; a 429 waits at least its retry-after;
   - a timed-out request is not repeated on the same model; it may go to the fallback once;
   - at most `max_attempts` provider calls per question, primary and fallback combined;
   - a per-request cost cap: when the cost so far (counting the likely cost of timed-out attempts) has
     reached `max_cost_usd`, stop and raise `BudgetExceeded`;
   - every attempt is written to `attempt_log`, including discarded ones, with `outcome`,
     tokens, `cost_usd` and `discarded`; a timed-out attempt gets an estimated (worst-case) cost.
3. Verify with `make test` and `make demo` (billed cost should match the cost of delivered answers).
4. Write `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- A 1,900-token answer is billed once; 400 is called once; 429 waits its retry-after; 529 backs off.
- No more than 3 calls per question; timeouts move to the fallback; the cost cap raises `BudgetExceeded`.
- Every attempt is logged, including timeouts with a non-zero estimated cost.
- `ANSWER.md` names the mechanism with numbers from the evidence and rules out the red herring.

## How to run

```bash
make setup     # shared Python venv
make report    # the usage export grouped by request
make demo      # replay traffic through your gateway on a fake clock
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade genai/w3-t1
make clean
```
