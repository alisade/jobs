# Rubric: genai/w6-c1 Catalog enrichment with validated structured output
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Contract and retry | 10 | Full: constraints declared on the model (Literal or validator for the taxonomy, `extra="forbid"`, lengths, ranges), the parse step separates JSON errors from schema errors, the retry prompt carries a concise field-level error, exactly one retry. Partial: retries without the error or retries unbounded. |
| 3 | Grounding checks | 15 | Full: unit-aware quantity extraction with a tolerance, word-boundary matching for materials and colors, banned vs conditional claims kept separate, all reasons collected (not first-only). Partial: substring checks that would pass "nylon" for "silnylon" or miss unit conversion. |
| 4 | Idempotency and budget | 10 | Store keyed by SKU + source hash, review outcomes remembered too (no nightly re-billing), budget checked before each call, skipped items reported in order. |
| 5 | ANSWER.md | 15 | Full: discusses schema-constrained decoding vs validate-and-retry, the review queue's load and how to measure its precision, sampling published items for QA, prompt and taxonomy versioning (re-run triggers), and what this means for the merchandising team. Partial: generic. |
Total: 100
