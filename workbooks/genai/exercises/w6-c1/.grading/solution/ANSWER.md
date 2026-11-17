# ANSWER: genai/w6-c1 Catalog enrichment with validated structured output

## Approach

I treated the model as an untrusted extractor and built three gates around it: a strict schema, a
deterministic grounding check against the supplier text, and a human review queue for anything that
fails. Each gate has its own tests. I wrote the fixtures for the failure modes the pilot hit: a
"45 L" cooler that was really 45 qt, and "eco-friendly" on a product that does not support it.

## Fix

- `models.py`: the taxonomy as a `Literal`, `extra="forbid"`, title at most 80 characters, description
  at most 400, positive quantities, confidence between 0 and 1.
- `pipeline.py`: parse, then validate. One retry with field-level errors (`title: String should have at
  most 80 characters`), then `invalid_output`. The store is keyed by SKU and source hash and remembers
  published and review outcomes. Spend is checked before every call, and skipped items are reported in
  order.
- `checks.py`: unit-aware quantity matching within 2 percent, word-boundary matching for materials and
  colors, always-banned claims, waterproof only when the supplier says it, and low confidence. All
  reasons are collected.
- `make run`: 2 published and 3 sent to review with clear reasons. A second run makes 0 model calls.

## Trade-offs / what I would do in production

- Schema-constrained output from the provider would remove most parse retries, but not grounding
  errors. The checks stay the legal control.
- The checks will have false positives, for example a color word that the supplier misspells. I would
  measure review precision and tune the checks, not loosen the rules.
- I would sample 2 percent of published items for weekly human QA, and version the prompt and the
  taxonomy so a change triggers a targeted re-run.
- The cost cap can overshoot by one call. Estimating tokens before each call would make it strict.
