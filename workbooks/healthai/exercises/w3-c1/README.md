# healthai/w3-c1 - X12 278-like request to a Da Vinci PAS-shaped FHIR Bundle

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 3 (Mon FHIR R4 Bundles; Wed Da Vinci PAS; Thu X12 278 and code sets)

## Scenario

Kestrel Health Plan (fictional) still receives most prior authorization requests as X12 278 through a
clearinghouse, while its new PA engine speaks FHIR (Da Vinci PAS: a Bundle around a Claim with
`use = preauthorization`). CMS-0057-F pushes payers to a FHIR Prior Authorization API by 2027, so for
a while both arrive. You write the adapter that turns a 278 request into the PAS-shaped Bundle the engine
consumes, and list what does not map cleanly.

X12 implementation guides are licensed, so this exercise uses a **simplified 278-like format** written
for the workbook. It keeps the real envelope rules and segment names but is not the X12 standard.

## The 278-like format

- The interchange starts with `ISA`. The 4th character is the element separator; ISA has 16 elements;
  the first character of ISA16 is the component separator and the next character is the segment
  terminator. Line breaks between segments may or may not be present.
- `BHT*0007*13*<trace id>*<CCYYMMDD>*<HHMM>`: trace id and creation date.
- `NM1*X3*2*<payer name>*****PI*<payer id>` (payer), `NM1*1P*1*<last>*<first>****XX*<NPI>` (requesting
  provider), `NM1*IL*1*<last>*<first>****MI*<member id>` (subscriber), `DMG*D8*<birth CCYYMMDD>*<M|F>`.
- `UM*HS*I*<service label>*<level>`: level `U` = expedited (urgent), blank = standard.
- `HI*ABK:<code>*ABF:<code>...`: ICD-10-CM codes without the dot; `ABK` principal, `ABF` other.
- `DTP*472*D8*<CCYYMMDD>` service date, or `DTP*472*RD8*<CCYYMMDD>-<CCYYMMDD>` service period.

## Your task

Implement `parse_x12(text)` and `to_pas_bundle(text) -> (bundle, warnings)` in `pas/mapper.py`:

1. Separators from the ISA header; reject text that is not an interchange (`ValueError`/`X12Error`).
2. A Bundle of `type: collection` with `urn:uuid:` fullUrls (deterministic: same input, same ids; use
   `uuid5` with the given namespace) and references that all resolve inside the Bundle: Claim, Patient,
   Coverage, Organization (payer), Practitioner (requester), ServiceRequest and one Condition per
   diagnosis.
3. Claim: `status active`, `use preauthorization`, type professional, `created` from BHT, `patient`,
   `provider`, `insurer`, `priority` (`stat` when level `U`, else `normal`), `insurance[0]` focal with
   the Coverage, `diagnosis` in order with the principal first (`sequence` 1..n), one `item` with
   `productOrService.text` = the service label (no codes: it is a label) and `servicedDate` or
   `servicedPeriod`.
4. Condition codes in `http://hl7.org/fhir/sid/icd-10-cm` with the dot restored (`M5416` -> `M54.16`).
   Patient identifier in the member-id system, birthDate and gender from DMG; Practitioner NPI in
   `http://hl7.org/fhir/sid/us-npi`; Coverage `subscriberId`.
5. Dates CCYYMMDD -> FHIR `YYYY-MM-DD`; an impossible date is an `X12Error`. Missing HI or missing
   subscriber is an `X12Error` naming the segment. Never a bare `KeyError`/`IndexError`/`StopIteration`.
6. `warnings`: human-readable notes for what does not map cleanly (at least: the service label is not a
   coded procedure, the 278 has no coverage period, level of service mapped to priority).

`pas/bundle_check.py` (given) is a structural checker the tests use; it is not a full PAS validator.

## Acceptance criteria (what the grader checks)

Both good fixtures pass `problems()` with no findings; references, codes, dates, priority, identifier
systems and diagnosis order are right; separators come from ISA; ids are deterministic; the three bad
fixtures raise `X12Error` with a useful message.

## Run

```
make setup && make test
# fill in ANSWER.md (include your "does not map cleanly" list), then: /grade healthai/w3-c1
make clean
```
