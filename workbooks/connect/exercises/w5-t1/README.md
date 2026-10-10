# connect/w5-t1 - The help desk bot quotes HR-only and retired articles

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 5 (Wed: Knowledge Bases - metadata filtering, sync, permission-aware retrieval)

## Symptom

Tuesday 2026-10-07, InfoSec opened a SEV-2: the employee portal chat bot (Connect chat -> Lambda
-> Bedrock knowledge base `KBLFGHELP01` -> Converse) showed a Finance business partner an
HR-only payroll article, and told a controller to "call the desk to have an RSA token shipped"
(RSA tokens were retired in 2024). Containment dropped five points since Monday. The data
platform team says last night's ingestion was fine apart from three unrelated failures;
contact center engineering says the retriever has not changed in two weeks. InfoSec wants the
root cause, the blast radius and a fix by end of day. Start with `incident/PAGE.txt`.

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the Slack thread |
| `incident/retrieval-log.jsonl` | the retriever's structured log for the replayed traffic (filter, counts, returned metadata) |
| `incident/sidecars/` | the `<article>.html.metadata.json` sidecars the exporter wrote to S3 |
| `incident/ingestion-jobs.json` | the last two KB ingestion jobs (ListIngestionJobs export) |
| `incident/model-invocation-log-sample.json` | one Bedrock model invocation log record |
| `incident/dashboard.txt` | CloudWatch dashboard export |
| `incident/release-*.md`, `incident/exporter-2026.10.05.diff` | what shipped and when |
| `src/exporter.ts` | ServiceNow KB -> S3 objects + metadata sidecars (data platform) |
| `src/retriever.ts` | entitlement filter + Retrieve call (contact center eng) |
| `src/kbsim.ts` | local stand-in for the knowledge base: recorded vector ranking per query, then the metadata filter, then `numberOfResults`. Environment, not a suspect. |
| `config/metadata-schema.json` | the metadata contract InfoSec signed off. Do not change it. |
| `data/` | the ServiceNow KB export, recorded scores and replay traffic |

## Your task

1. Find the root cause with evidence: which bytes changed, why the filter stopped matching for
   some callers and not others, and how that turned into other departments' and retired content
   reaching callers. Separate the trigger from any latent defect it exposed.
2. Rule out the red herring with a reason.
3. Fix `src/exporter.ts` and/or `src/retriever.ts` so the system fails closed and the contract
   cannot silently drift again. `make replay` must show no leaks.
4. Size the blast radius from the logs: which callers, which articles, since when.
5. Write `ANSWER.md`: Approach, Root cause (commands and excerpts), Fix (and verification),
   Trade-offs / production follow-ups.

## Acceptance criteria (what the grader checks)

- Sidecars carry exactly the schema's attributes; department is filterable under the key the
  retriever uses; status and region normalized.
- Every retriever filter key exists in the schema; an empty filtered result hands off without
  any unfiltered retry.
- Replay: no caller receives an article outside their entitlements or a retired article; Finance,
  HR and Legal users find their department articles again.
- `ANSWER.md` names the mechanism precisely, with evidence and blast radius. A fixed system with a
  hand-waved explanation does not pass.

## How to run

```bash
make setup     # shared toolchain + incident/ bundle generated from this checkout
make replay    # replay the traffic through this checkout (run it before and after your fix)
make test      # visible checks
# from workbooks/: /grade connect/w5-t1
make clean
```

Useful: `grep '"fallback":"unfiltered"' incident/retrieval-log.jsonl | wc -l`, `jq -c '{caller,query,filteredCount,fallback}' incident/retrieval-log.jsonl`, `cat incident/sidecars/KB0020456.html.metadata.json`.
