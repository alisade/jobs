# Reference: genai/w6-c1

Reference files: `.grading/solution/enrich/{models,checks,pipeline}.py`.

- **Contract:** `category` is a `Literal` of the taxonomy, with `extra="forbid"`, length and range
  constraints. The parser keeps "not JSON" apart from "JSON but invalid", and the retry prompt gets
  `loc: msg` pairs (for example `title: String should have at most 80 characters`). There is exactly one
  retry, and two failures give `invalid_output`.
- **Grounding:** a regex extracts quantities with units (kg, g, lb, oz; L, ml, qt, gal), converts them
  and compares within 2 percent. Materials and colors match on word boundaries. Banned claims are always
  rejected. "Waterproof" is rejected only if the supplier text does not say it. All reasons are
  collected, so a reviewer sees everything at once.
- **Idempotency:** the store is keyed by SKU and remembers the outcome (published or review) with the
  source hash. Unchanged items are never re-billed, and a changed description is processed again.
- **Budget:** check spend before each call. The batch can overshoot by at most one call; say so, or
  estimate the next call's cost before making it.

Production notes: schema-constrained output (structured outputs or tool input schemas) removes most
parse retries but not grounding errors. The grounding checks are the legal control. Measure the review
queue (how many were really wrong), sample published items weekly, and version prompts and taxonomy so
a change triggers a targeted re-run.
