# ANSWER: healthai/w3-t1 PAs pended for "missing diagnosis"

## Approach

Compared the replay (81 pended for missing diagnosis) with the baseline (6/118), then dumped one oncology
Bundle and walked the engine's `diagnoses()` filter.

## Root cause

The PA-2230 refactor changed the mapper to `T.ICD10` = `http://hl7.org/fhir/sid/icd-10` (WHO ICD-10). The
engine filters on `T.ICD10CM` = `http://hl7.org/fhir/sid/icd-10-cm`. The codes are fine (`C34.90`), the
system is wrong, so the engine sees no diagnoses and pends every policy with a diagnosis rule: oncology
and cardiology. Spine and knee policies have no diagnosis rule, so they looked normal. The payer display
warning is a letter warning and never affects routing.

## Fix

Mapper uses `T.ICD10CM`. Replay: pended missing diagnosis 81 -> 9 (those 9 records have no diagnosis).
`tests/test_regression.py` asserts the system and that the engine routes the case as ready; it fails on
the released mapper.

## Trade-offs / what I would do in production

Re-route everything pended since the release and check expedited clocks. Add a mapper/engine contract
test and terminology validation in CI. Refactors labelled "no behaviour change" still need tests that pin
behaviour.
