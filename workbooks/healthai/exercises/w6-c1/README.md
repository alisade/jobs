# healthai/w6-c1 - PHI de-identification for logs, prompts and traces

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 6 (Mon minimum necessary; Tue de-identification; Wed PHI flow map)

## Scenario

Kestrel Health Plan (fictional) wants to export LangGraph traces and application logs to a tracing tool
that is **not** covered by the plan's BAA, and to build eval datasets from real cases. Security's
condition: nothing that leaves the PHI boundary may carry an identifier, and each agent step may see only
the fields it needs (HIPAA minimum necessary). In production you would use the Healthcare API
de-identify operation and Sensitive Data Protection; this exercise builds the in-process layer that sits
in front of every log handler, prompt builder and span exporter, so you know exactly what those services
must catch.

## What you have

| Path | What it is |
|---|---|
| `deid/core.py` | the first draft (keep the public API) |
| `deid/settings.py` | the pseudonymization key (from env) and the as-of year |
| `fixtures/bundle.json` | a synthetic FHIR bundle: Patient with identifiers, telecom, address, a 92-year-old birth date, conditions, a medication, an observation and a ServiceRequest whose note mentions the member and a relative |
| `tests/` | visible tests; `conftest.py` gives you a captured logger with your filter on the handler |

## Your task

1. `pseudonymize_member_id`: keyed HMAC-SHA256, `MBR-` + 12 hex chars; deterministic per key.
2. `names_from_patient`: every given and family name (and `text` if present).
3. `redact_text(text, known_names, key)`: known names (any case, hyphen parts too) -> `[NAME]`; member ids
   -> pseudonym; MRN, SSN (dashed or 9 digits after "SSN"), phone numbers (common US formats), emails,
   dates more specific than a year (ISO, `m/d/yy`, `March 14, 2026`, `14 Mar 2026`), street addresses, ZIP
   codes, and ages over 89 (`[AGE-OVER-89]` or similar). Clinical content must survive: ICD-10-CM codes,
   doses, durations, scores, policy ids, ages under 90.
4. `redact_obj`: recursive over dicts and lists; identifier keys (`name`, `birthDate`, `telecom`,
   `address`, `identifier`, ...) are replaced wholesale.
5. `age_band(birth_date)`: decade bands, `90+` at 90 and over.
6. `minimum_necessary(bundle)`: exactly `member_token, age_band, sex, conditions, medications,
   observations, service, notes` (notes redacted); `build_prompt` uses it.
7. `RedactingFilter`: redact the formatted message (`msg % args`), exception text and string `extra`
   attributes before any handler formats the record.
8. `scrub_span_attributes`: identifier-named attributes dropped, string and nested values redacted,
   numbers and case ids kept.

## Acceptance criteria (what the grader checks)

- A paragraph with every planted identifier type, in several formats and cases, comes out clean;
  clinical content is preserved.
- Pseudonyms are keyed and deterministic; nested objects are clean.
- The prompt and the minimum-necessary context carry no identifier.
- Identifiers passed to the logger as args, in `extra=`, in an f-string and inside an exception never
  reach handler output; span attributes are scrubbed.

## Run

```
make setup && make test
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade healthai/w6-c1
make clean
```
