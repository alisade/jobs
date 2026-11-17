# Reference: healthai/w3-t1

PA-2230 replaced the mapper's local `ICD10_SYSTEM` (ICD-10-CM) with `T.ICD10`, the WHO ICD-10 URI, while
the engine was correctly moved to `T.ICD10CM`. Codes still look right (`C34.90`), only the system
differs, so the engine's `diagnoses()` filter returns nothing and every policy with a diagnosis rule
pends. Replay: 81 pended before, 9 after (the 9 records really have no diagnosis). The payer display
warning is a letter-formatting warning; the runner never routes on warnings.

Follow-ups: re-route the cases pended since 2026-11-17 18:00 and check expedited clocks; add a
mapper/engine contract test and a terminology check (system + code) in CI; ICD-10-CM is the HIPAA code
set for US diagnoses, WHO ICD-10 is not.
