# Reference: connect/w5-c3

Reference config: `.grading/solution/tuning/agent.yaml`. On the visible set it reaches accuracy 0.943,
containment 0.509, no misroutes or hallucinations, p95 1129 ms (159 prompt tokens); on the holdout
0.92 accuracy, 0.44 containment, 1 misroute in 25.

What great work shows:

- Error analysis first: baseline accuracy 0.094 is all fallbacks (threshold 0.9 and one-word
  descriptions), so the first lever is vocabulary (descriptions + examples), the second the threshold.
- Disambiguating shared words: "password" appears in reset and unlock utterances; "access" in
  request-access and outage wording; "open" and "many" are noise words that pull out-of-scope
  questions into real intents. Descriptions describe meaning and distinguishing context.
- Threshold from the trade-off: lower raises containment and misroutes together; 0.5 is where
  misroutes stay at 0 on the visible set.
- Retrieval: topK 1 misses the right article whenever it ranks 2nd-4th; topK 4 with minScore 0.4
  catches it at +240 ms. Without citations, a lower topK turns misses into hallucinations; with
  citations required they become handoffs.
- Latency: every example costs prompt tokens on every turn; the budget forces choosing the
  examples that fix real confusions.
- Real-world loop: same discipline with a real AI agent prompt: labeled transcripts, frozen
  holdout, A/B through the flow, LLM-as-judge for answer quality, CI gates on the metrics.
