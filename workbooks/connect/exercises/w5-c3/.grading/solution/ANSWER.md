# ANSWER: connect/w5-c3 Tune the help desk AI agent against an eval set

## Approach

Baseline: accuracy 0.094, containment 0 - every in-scope utterance fell back (threshold 0.9, one-word
descriptions). Classified errors as fallback / misroute / hallucination and changed one lever at a time.

## Fix

1. Descriptions by meaning (30-token budget), no examples, threshold still 0.9: acc 0.094 -> 0.094 -
   descriptions alone do not help while the threshold rejects everything.
2. Threshold 0.9 -> 0.55 (plus retrieval topK 4, minScore 0.4, citations on): acc 0.887, containment 0.453,
   misroute 0, p95 1061 ms, 91 prompt tokens.
3. Added 3-4 examples per intent aimed at the remaining confusions (outage vs how-to wording, "approved"
   for ticket status, "starter" for access): acc 0.925, containment 0.491, p95 1129 ms, 159 tokens.
4. Threshold 0.55 -> 0.5: acc 0.943, containment 0.509, misroute 0, hallucination 0.
Holdout: accuracy 0.92, containment 0.44, misroute 0.04.

## Trade-offs / what I would do in production

Refresh the labeled set monthly from transcripts with a frozen holdout; A/B new prompts with a percentage
split in the flow; LLM-as-judge / Bedrock RAG evaluation for answer faithfulness and citation precision;
track containment against CSAT and transfers-with-context; keep prompt tokens in check for cost and latency.
