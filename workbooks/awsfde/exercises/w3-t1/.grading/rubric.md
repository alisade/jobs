# Rubric: awsfde/w3-t1 A new tenant sees another tenant's documents in answers
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh |
| 2 | Root cause identified | 25 | Full: the ASK-412 fallback in retrieve_context retries Retrieve with no filter when the filtered call returns no chunk above MIN_SCORE; only tenants with few documents (Delta) fall below the floor, so established tenants never trigger it. Partial (10): "missing filter" without the conditional fallback mechanism or why only Delta. Zero: blames chunking/re-ingest, metadata sidecars or the KB. |
| 3 | Evidence | 20 | Full: quotes kb.log lines with no filter for the affected request ids (req-0009, req-0010, req-0012), the paired retrieval.log entries (filtered true with usable 0, then filtered false), 15 calls for 12 questions, and the diff against the 2026.11.03 version. Partial: one source. |
| 4 | Red herring handled | 5 | Rules out ASK-398: ingestion job COMPLETE, 14 documents and 14 metadata files scanned, 0 failed; established tenants unaffected; metadata intact in kb.log results. |
| 5 | Fix quality | 10 | Full: no unfiltered path at all; no widening via orAll/notEquals; honest no-answer for thin tenants; defense-in-depth drop of foreign/untagged chunks with an error log. Partial: removes the fallback only. Zero: lowers MIN_SCORE or adds Delta-specific code. |
| 6 | Exposure statement and prevention | 10 | Full: exact statement (Acme Foods document chunks shown to Delta Outfitters users on 3 requests: returns-policy/holiday-cutoffs, damage-claims, returns-policy; no Delta data exposed to others; window since 2026-11-10 release), notify Acme too; prevention: a cross-tenant test suite in CI, a single request builder that cannot omit the filter, alarm on foreign_chunk_dropped, security review rule for retrieval changes, product answer for thin tenants (onboarding checklist, "documents not loaded" message). Partial: generic. |
Total: 100
