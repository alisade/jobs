# Reference: audit/w1-c1

The reference files are in `.grading/solution/controlpilot/`.

Key points:

- **Contract.** `ChangeEvidence` has no defaults: `approver: str | None` with no default means the key
  is required but may be null. The draft's `tests_passed: bool = True` and `approver: str = ""` are the
  classic audit bug: a missing key becomes a passing value. `extra="forbid"` turns a model that starts
  adding `"conclusion": "effective"` into a validation error you retry, instead of silently accepted
  noise. `AwareDatetime` rejects naive timestamps, which are ambiguous across the entity's time zones.
- **Request.** `response_schema=ChangeEvidence` constrains generation, but the code still validates
  `response.text` itself: constrained decoding is not a guarantee (truncation, enum drift, unsupported
  schema keywords are ignored by the server), and `response.parsed` is silently None on failure.
  Automatic function calling is disabled so every tool call is visible, allow-listed and logged.
- **Loop.** Tool turns and format attempts are budgeted separately. Disallowed tools get an error
  response the model can act on; tool exceptions go back as data. MAX_TOKENS is retryable (ask again,
  maybe with a larger budget); SAFETY/RECITATION are not. The retry message lists the Pydantic errors
  verbatim, which is what makes the second answer converge.
- **Grounding check.** A schema-valid answer about the wrong change (`CHG-999999`) is still wrong; the
  code checks the ids against the sample.
- **Attributes.** Compare instants (`astimezone(UTC)`), never strings: S06's approval at 09:30+02:00 is
  07:30Z, before an 08:00Z deploy. Equality is an exception (not strictly before). Identities resolve
  through the directory, so `j.ortiz` and `jortiz@meridianfreight.example` are the same person (S05
  is a real SoD exception: self-approved "per on-call"). Unknown identities are not_evaluable, which
  routes the sample to a human instead of guessing.

Interview angle: "Why not let the model decide pass/fail?" Because the conclusion must be
reproducible and explainable to an external auditor; the model's job is reading messy evidence, and
its output is a typed claim with a citation that a deterministic rule consumes.
