# healthai/w3-t1 - Oncology and cardiology PAs pended for "missing diagnosis"

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 3 (Mon FHIR R4 resources; Thu ICD-10-CM vs ICD-10 and code systems)

## Scenario

After release 2026.11.1 at Kestrel Health Plan (fictional), almost every oncology and cardiology prior
authorization is routed to "pended: missing diagnosis", although providers sent diagnoses. Nurses are
re-routing about 40 cases a day by hand, and some are expedited, so the 72-hour clock is running. The
platform team suspects a new validator warning. Read `incident/ticket.md`.

## What you have

| Path | What it is |
|---|---|
| `incident/` | the ticket, release notes with a diff excerpt, the previous routing summary; `engine-run.log` after `make setup` |
| `pipeline/mapper.py`, `pipeline/terminology.py` | intake record -> FHIR Bundle (Patient, Coverage, Claim, Conditions) |
| `pipeline/validator.py`, `pipeline/criteria_engine.py`, `pipeline/run.py` | structural checks, the rule-based router, the runner |
| `data/requests.json` | 120 synthetic intake records (from `make setup`) |
| `findings.json` | your machine-checked findings |

## Your task

1. `make setup`, compare `engine-run.log` and `make replay` with `incident/routes-baseline.txt`.
2. Find the root cause and decide whether the payer-display warning matters, with evidence (a Bundle
   excerpt and the engine code path).
3. Fix it, re-run `make replay`, and fill in `findings.json`: file, wrong and right value, pended
   "missing diagnosis" count before and after.
4. Add `tests/test_regression.py`: a test that passes on your fix and **fails on the released mapper**
   (the grader runs it against both).
5. `ANSWER.md`: root cause, evidence, impact on cases already pended, and prevention.

## Acceptance criteria (what the grader checks)

- Conditions carry ICD-10-CM codings with the dot restored; the engine sees them; routing is back to
  the baseline shape (9 genuinely missing diagnoses on this data).
- `findings.json` is right; your regression test passes on the fix and fails on the released code.

## Run

```
make setup && make replay && make test
# fill in ANSWER.md and findings.json, then: /grade healthai/w3-t1
make clean
```
