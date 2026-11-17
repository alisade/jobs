# Rubric: healthai/w3-c1 X12 278-like request to a Da Vinci PAS-shaped FHIR Bundle
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Mapping quality | 15 | Clear segment-to-resource mapping, correct systems (ICD-10-CM, NPI), principal diagnosis first, deterministic ids, no CPT descriptors or invented codes. |
| 3 | Robustness | 10 | Separators from ISA, typed `X12Error` with segment names, no bare lookups that throw KeyError/StopIteration on bad input, no PHI in exception messages beyond the segment id. |
| 4 | ANSWER.md | 20 | A real "does not map cleanly" list (e.g. coverage period, service labels vs coded procedures, level of service vs priority, multiple service lines, attachments/PWK, provider roles), where real validation happens (HL7 validator with the PAS and US Core packages), and how the ClaimResponse maps back to a 278 response. |
Total: 100
