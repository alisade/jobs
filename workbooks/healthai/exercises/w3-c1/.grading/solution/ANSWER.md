# ANSWER: healthai/w3-c1 X12 278-like request to a PAS-shaped Bundle

## Approach

Separators come from ISA (position 3, and the character after ISA16). Segments are looked up by id and
qualifier; each resource gets a uuid5 fullUrl from trace id + kind, so references are known before the
resources are built and the output is deterministic.

## Fix

Claim with use preauthorization, priority from UM level of service, focal insurance, diagnoses with the
principal (ABK) first and the dot restored, servicedDate or servicedPeriod, ServiceRequest linked via
supportingInfo. Bad input raises X12Error naming the segment; the checker reports no problems on both good
fixtures.

## Trade-offs / what I would do in production

Does not map cleanly: coverage period (absent from the 278), service labels (need HCPCS or a licensed
procedure code), level of service (PAS also carries it as an extension), attachments, multiple service
lines and provider roles. Validate against the PAS and US Core packages with the HL7 validator in CI.
Map ClaimResponse back to a 278 response for clearinghouse submitters. Keep member names out of error logs.
