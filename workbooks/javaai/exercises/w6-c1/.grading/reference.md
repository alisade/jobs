# Reference: javaai/w6-c1

Files in `.grading/solution/tuneval/`: `tuning.py`, `evaluate.py`.

| candidate | valid | correct | grounded | USD / 1,000 | p50 ms | p95 ms |
|---|---|---|---|---|---|---|
| prompt-flash | 0.88 | 0.84 | 0.84 | 0.9241 | 2336 | 2984 |
| fewshot-flash | 0.96 | 0.90 | 0.88 | 1.4919 | 3053 | 10058 |
| tuned-flashlite | 1.00 | 0.90 | 0.98 | 0.1332 | 995 | 3579 |

Dataset: 309 in, 6 duplicates, 3 leaked held-out records, 270 train, 30 validation.

## The decision

Tuned Flash-Lite meets both thresholds at about a tenth of few-shot's cost and the lowest median
latency. Caveats a senior answer names: 50 items gives roughly +-8 points at 95% on a proportion
near 0.9, so few-shot and tuned are statistically tied on correctness; the tuned model was trained on
a draft that still contained 3 held-out items (its scores may be inflated: re-tune on the clean set
and re-run before shipping); a tuned model is pinned to its base version and must be re-tuned when
that version retires; tuning teaches format and style, not new facts (lesson knowledge stays in
retrieval); per the docs, set thinking to minimal on tuned tasks.

## Interview angles

- "When would you not tune?" Small data, changing requirements, knowledge that changes: prompt + RAG.
- "How do you know the tuned model is better?" Same held-out set, same scorer, never by eye; plus a
  judge rubric or human sample for distractor quality, which deterministic checks miss.
