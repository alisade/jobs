# ANSWER: healthai/x-1 LoRA vs prompting for ICD-10-CM extraction

## Approach

Computed cost at the actual volume first, then read quality by slice against the constraint that missed
rare codes are the costly error.

## Fix

Ship the prompted model: $183 vs $620 a month at 38k notes, and rare-code F1 0.701 vs 0.488.

## Trade-offs / what I would do in production

Volume above about 129k notes a month, a latency-critical use, or a LoRA run that closes the rare-code gap
(more rare examples, constrained decoding) would change the decision. Next experiment: a hybrid router
with LoRA for confident top-50 predictions and the large model otherwise, evaluated by slice.
