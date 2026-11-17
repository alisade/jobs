# awsfde/w3-t1 - A new tenant sees another tenant's documents in answers

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 3 (Wed: metadata filters and multi-tenancy; Thu: vector store choices; Fri: retrieval evals)

## Symptom

Delta Outfitters went live on Tidewater Ask three days ago. Their director of customer care opened a
P1 security ticket: answers about returns and damage claims quote policies that are not theirs, and
one citation link contains `/tenants/acme-foods/`. The three established tenants have used Ask for
months without a single report like this. Delta's CISO wants a precise answer today: what was
exposed, to whom, and is it fixed. Read `evidence/TICKET-5521.txt` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/TICKET-5521.txt` | the customer ticket and the account team's note |
| `evidence/release-2026.11.10.md` | what shipped this week |
| `evidence/ingestion-job-2026-11-10.json` | the KB re-ingest job (a `GetIngestionJob` response) |
| `evidence/retrieval-py-2026.11.03.py` | `retrieval.py` from the release before |
| `evidence/questions.jsonl` | the questions customers asked in the reported window |
| `ask_service/` | this checkout: retrieval and answer assembly running in prod |
| `kb_sim/` | a local Knowledge Base with the `Retrieve` request and response shapes, documents with `.metadata.json` sidecars, deterministic scoring. Treat it as the environment, not the suspect. |
| `run/` | created by `make setup`: `summary.txt`, `answers.jsonl`, `retrieval.log` (service log), `kb.log` (one line per Retrieve call as the KB saw it) |

## Your task

1. Find the root cause and prove it from the logs and the code: which requests reached the KB
   without the tenant filter, why only Delta is affected, and why the established tenants never saw it.
2. Decide whether the re-ingest with hierarchical chunking (ASK-398) is involved, with evidence.
3. Fix `ask_service/` so no path can retrieve another tenant's documents, while Delta still gets an
   answer when its own documents cover the question and an honest "not found" when they do not.
4. Verify with `make test` and `make replay`.
5. Write `ANSWER.md`, including the exposure statement for the CISO (which tenant's documents were
   shown to which tenant, for which requests) and how you would stop this class of change shipping again.

## Acceptance criteria (what the grader checks)

- Every Retrieve call carries a filter that matches only the caller's tenant, one call per question.
- No answer cites another tenant's document; thin-tenant questions get the no-answer text.
- A mis-tagged or untagged chunk returned by the KB is never used as context.
- Established tenants and Delta's covered questions still answer; the score floor still applies.
- `ANSWER.md` names the mechanism with evidence (log lines, code), rules out the re-ingest, and
  gives a precise exposure statement and prevention plan.

## How to run

```bash
make setup     # shared venv + replay of the reported questions into run/
make test
make replay    # after your fix
# from workbooks/: /grade awsfde/w3-t1
make clean
```
