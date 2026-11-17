# Rubric: genai/w3-t1 The assistant's model bill went up 9x overnight
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (three guards pass on the starter) |
| 2 | Root cause identified | 25 | Full: the gateway's fixed 10 s read timeout is shorter than a 2048-token comparison takes to generate (0.6 s + 7 ms x ~1,900 tokens, about 14 s). The client gives up, but the provider finishes and bills the request. The retry loop treats the timeout as retryable, with no backoff, 4 times on the primary and 4 times on the fallback, so each comparison question bills 8 full generations and still fails. The trigger was release 2026.11.10 (max_tokens 512 to 2048, comparisons); the gateway was already wrong. Partial (10-15): "retries cost money" or "timeouts" without billed-but-discarded generations and the multiplier. Zero: traffic, provider pricing, or a provider outage. |
| 3 | Evidence | 20 | Full: usage-export rows with one fingerprint billed 8x across both models, durations of 14 s against a 10 s timeout; gateway log attempt=1..4 per model then a 500 after 70 s; traffic.txt requests per question going from 1.00 to 3.56 while questions per session stays flat; `make demo` numbers before and after. Partial: one or two of these. |
| 4 | Red herring ruled out | 5 | The email added about 30 percent more sessions; 1.3x traffic cannot make 9x spend. Requests per question is the number that moved. |
| 5 | Fix quality | 10 | Timeout derived from max_tokens (or streaming with an idle timeout), retry only 429/529 with exponential backoff, jitter and retry-after, never 400, a timeout not repeated on the same model, one attempt budget shared with the fallback, a cost cap that counts the estimated cost of timed-out attempts, every attempt logged. No edits to provider/pricing/clock. |
| 6 | Prevention | 10 | Concrete: an alert on billed tokens vs delivered tokens (or provider requests per question), retry budgets owned by one layer, streaming for long answers, a load test with production-length outputs before prompt changes, per-request cost in traces for finance. Partial: generic "monitor cost". |
Total: 100
