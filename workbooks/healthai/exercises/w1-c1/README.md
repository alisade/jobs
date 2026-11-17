# healthai/w1-c1 - PA intake API with typed requests and the CMS-0057-F clock

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 1 (Tue Pydantic v2, Wed FastAPI, Thu CMS-0057-F)

## Scenario

Kestrel Health Plan (fictional) is replacing a fax-and-portal intake with an API that providers' systems
call. Every prior authorization (PA) request becomes a case with a decision deadline, because since
January 2026 CMS-0057-F requires decisions within **72 hours for expedited** and **7 calendar days for
standard** requests for Medicare Advantage, Medicaid and CHIP managed care and fee-for-service (QHP
issuers on the federally facilitated exchanges are outside those timeframes). A first draft exists; it
accepts only imaging requests, trusts every field, and computes deadlines with naive datetimes.

## What you have

| Path | What it is |
|---|---|
| `intake/models.py` | request and response models (finish them) |
| `intake/clock.py` | `compute_deadline(received_at, priority, plan_type, plan_tz)` (rewrite it) |
| `intake/app.py` | the FastAPI app (finish it) |
| `intake/eligibility.py` | a fake async eligibility client with synthetic members; do not change |
| `tests/` | visible tests with `httpx.AsyncClient` over `ASGITransport` and dependency overrides |

## Your task

1. **Models (Pydantic v2).** A shared base with `member_id` (`M-` plus 6 digits), `priority`
   (`expedited`|`standard`), `received_at` (timezone-aware; naive is a 422), `diagnosis_codes` (at least
   one; each an ICD-10-CM code shape `^[A-Z][0-9][0-9A-Z](\.[0-9A-Z]{1,4})?$`, normalized by stripping and
   upper-casing), `clinical_justification` (required, at least 20 characters, when expedited). Unknown
   fields are rejected. Three categories, discriminated on `category`:
   - `imaging`: `modality` in `mri|ct|pet`, `body_region` (2+ chars)
   - `medication`: `drug_name`, optional `hcpcs_code` (`^[A-Z]\d{4}$`, HCPCS Level II), `days_supply`
     strict int 1-365
   - `inpatient`: `admit_date` (date), `expected_los_days` strict int 1-60

   `PARequest` must be an `Annotated[Union[...], Field(discriminator="category")]`.
2. **Decision clock.** Raise `ValueError` for a naive datetime or unknown priority. `plan_type ==
   "qhp-ffe"` returns `None` (no federal clock). Expedited: exactly 72 elapsed hours. Standard: 7
   calendar days on the wall clock of the plan's time zone `plan_tz` (same local time of day, even across
   a DST change). Always return an aware UTC datetime.
3. **API.** `POST /v1/pa-requests` returns 201 with `CaseOut`. Look up eligibility through the
   `get_eligibility` dependency inside `asyncio.timeout(get_timeout())`; on timeout return 503 with
   `detail` mentioning eligibility. Inactive coverage is not rejected: `route: "eligibility-review"`.
   `clock` is `"none"` and `decision_due` null when there is no federal clock.
4. **Idempotency.** An `Idempotency-Key` header with the same body returns the same case (no second
   eligibility call); the same key with a different body is a 409.
5. **Lifespan.** Create the eligibility client, the case store and the idempotency store in a lifespan
   handler on `app.state`, and close the client on shutdown. `GET /v1/pa-requests/{case_id}` returns the
   case or 404.

## Acceptance criteria (what the grader checks)

- Every category validates; bad codes, ids, extra fields, non-strict ints and missing expedited
  justification are 422.
- Clock edge cases: QHP, DST spring forward and fall back, plan time zone different from the sender's
  offset, UTC output.
- 503 on eligibility timeout (bounded), idempotent replay and 409 conflict, lifespan opens and closes
  the client, state is per app lifespan.

## Run

```
make setup && make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade healthai/w1-c1
make clean
```
