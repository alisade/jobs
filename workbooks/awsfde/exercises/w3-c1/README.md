# awsfde/w3-c1 - Retrieval eval harness and a tenant-filtered Retrieve call

**Type:** coding | **Estimate:** 2 hours | **Study plan:** Week 3 (Mon: Knowledge Bases; Tue: chunking; Wed: metadata filters; Fri: retrieval evals)

## Scenario

Tidewater Ask answers questions from each tenant's documents through one Bedrock Knowledge Base on
S3 Vectors, with `tenant_id` set in every document's `.metadata.json` sidecar. The platform team
wants to switch the data source from fixed-size chunking to hierarchical chunking and asks you, the
FDE, for a number instead of an opinion: does retrieval get better, for every tenant, and is any
tenant ever shown another tenant's chunk?

You build two things: the one function every caller must use to build a `Retrieve` request (so the
tenant filter cannot be forgotten or bypassed), and an eval harness that runs a 20-question golden
set against both configurations and produces a go/no-go report the change board can read.

## What you have

| Path | What it is |
|---|---|
| `fixtures/golden.json` | 20 golden questions across three tenants, each with the S3 URIs of the documents that answer it |
| `fixtures/recorded-fixed.json`, `recorded-hierarchical.json` | recorded `retrievalResults` from the two KB configurations |
| `kb_eval/fake_kb.py` | `RecordedKnowledgeBase.retrieve(**params)`: validates your request against the real `Retrieve` input shape from botocore, then returns the recording (done) |
| `kb_eval/request.py` | `build_retrieve_request()` - **your work (Part A)** |
| `kb_eval/harness.py` | metrics, leak check, report, compare, gate - **your work (Part B)** |
| `kb_eval/run.py` | `make eval`: runs both configs, writes `run/report-*.json` and `run/compare.json` (done) |
| `scripts/make_fixtures.py` | how the fixtures were generated (read it only if you are curious) |

## Your task

**Part A: `build_retrieve_request(kb_id, tenant_id, query, user_filters, k)`**

- `retrievalQuery.text` is the query (empty or blank raises `ValueError`); `vectorSearchConfiguration.numberOfResults = k`, 1 to 100.
- The filter **always** contains `{"equals": {"key": "tenant_id", "value": <verified tenant>}}`.
- User filters (a list of `RetrievalFilter` dicts, for example `doc_type` or `year`) are ANDed with it.
  `andAll` needs at least two members, so with no user filters the tenant filter is used on its own.
  A user `orAll` stays inside the `andAll`; it must never wrap the tenant filter.
- Any user filter that mentions `tenant_id` anywhere, even nested, raises `ValueError`.

**Part B: the harness in `kb_eval/harness.py`**

- `unique_ranked_uris()`: the KB returns chunks; several chunks of one document count once, at the rank
  of the first.
- `recall_at_k()` over unique documents, `reciprocal_rank()` (0.0 when nothing expected is retrieved).
- `leaks()`: any result whose metadata `tenant_id` differs from the caller's, or is missing, is a leak.
- `evaluate()`: one `Retrieve` per golden question, through `build_retrieve_request`, and the report
  shape in the docstring (means rounded to 4 places, per-tenant breakdown, leaks, per-question rows).
- `compare(baseline, candidate)`: deltas overall and per tenant, and leak counts.
- `gate(report, ...)`: no-go on any leak, on overall recall or MRR below the floor, or on any tenant
  below the per-tenant recall floor; return the reasons.

Then run `make eval`, read the two reports, and write your recommendation in `ANSWER.md`.

## Acceptance criteria (what the grader checks)

- Requests pass validation against the real `Retrieve` model; the tenant filter is present on every
  path and cannot be widened by a user filter.
- Metrics count documents, not chunks; edge cases (nothing retrieved, missing metadata) are right.
- The fixture run reproduces the expected recall for both configs and finds the one leaking question.
- The gate blocks a leak even when every metric is perfect, and enforces the per-tenant floor.
- `ANSWER.md` interprets the numbers and recommends what to do (including about the leak).

## How to run

```bash
make setup
make test
make eval      # after Part B: prints both configs and the gate decision
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade awsfde/w3-c1
make clean
```
