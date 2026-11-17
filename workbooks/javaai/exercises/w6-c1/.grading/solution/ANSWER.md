# ANSWER: javaai/w6-c1 Tune or prompt?

## Approach

Built the dataset with dedupe on normalized stems, a leakage check against held-out section text
(held-out records have no stem field), and a sha256(id) split. Then a strict parser and the scorer.

## Fix

    prompt-flash     valid 0.88  correct 0.84  grounded 0.84  $0.9241/1k  p50 2336  p95 2984
    fewshot-flash    valid 0.96  correct 0.90  grounded 0.88  $1.4919/1k  p50 3053  p95 10058
    tuned-flashlite  valid 1.00  correct 0.90  grounded 0.98  $0.1332/1k  p50 995   p95 3579
    pick: tuned-flashlite
Dataset: 309 in, 6 duplicates, 3 leaked, 270 train, 30 validation. 17/17 tests.

## Trade-offs / what I would do in production

Ship tuned Flash-Lite after re-tuning on the clean set (the draft contained 3 held-out items, so
its numbers may be inflated) and re-running this eval. With 50 items few-shot and tuned are tied on
correctness; cost (11x) and latency decide. Few-shot's p95 comes from long prompts. Tuning fixes format
and style; lesson facts stay in RAG. Next: a judge rubric for distractor quality and a human sample.
