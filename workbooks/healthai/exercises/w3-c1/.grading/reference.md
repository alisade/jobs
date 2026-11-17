# Reference: healthai/w3-c1

See `.grading/solution/pas/mapper.py`. Notes for the debrief:
- ISA is fixed-width in real X12, but reading the separator at position 3 and the terminator after ISA16
  works for both fixed-width and loose files.
- `uuid5(namespace, trace/kind/key)` gives stable fullUrls, so a retried request produces the same Bundle
  and idempotency is easy downstream.
- Real PAS requires profiles (PAS Claim, US Core Patient, etc.), extensions (level of service,
  certification type) and a `Claim/$submit` operation that returns a ClaimResponse Bundle. Validate with
  the HL7 FHIR validator and the IG package in CI; Pydantic shape checks are only a first gate.
- Does not map cleanly: coverage period, the service label (needs a coded procedure or HCPCS),
  level-of-service vs Claim.priority (PAS uses an extension too), attachments, multiple providers, and
  the 278's HL hierarchy itself (FHIR uses references, not nesting).
