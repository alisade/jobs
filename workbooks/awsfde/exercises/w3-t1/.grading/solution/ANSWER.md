# ANSWER: awsfde/w3-t1 New tenant sees another tenant's documents

## Approach

Read the ticket, then run/summary.txt: 15 Retrieve calls for 12 questions and 3 Delta answers citing
another tenant. Matched kb.log to retrieval.log by request id, then diffed retrieval.py against the
previous release.

## Root cause

ASK-412 added an unfiltered retry when the filtered Retrieve has no chunk >= MIN_SCORE (0.30).
kb.log shows three calls with "filter": null for req-0009, req-0010 and req-0012, each returning
s3://.../tenants/acme-foods/... URIs; retrieval.log shows "filtered": true, "usable": 0 followed by
"filtered": false for the same ids. Only Delta has so few documents that nothing clears the floor,
so the established tenants never hit the fallback. The re-ingest (ASK-398) is not involved: the job
is COMPLETE with 14/14 documents and metadata files scanned and 0 failed, and results carry correct
tenant_id metadata.

## Fix

Removed the fallback; every request carries the tenant filter; thin tenants get the no-answer text;
chunks whose tenant_id metadata is not the caller's are dropped and logged as an error. make test
passes; make replay shows 12 calls for 12 questions and 0 foreign citations, Delta 2 grounded and 3
no-answer.

## Trade-offs / what I would do in production

Exposure: Acme Foods excerpts shown to Delta Outfitters users in 3 answers since 2026-11-10; no Delta
data exposed; notify both tenants. Prevention: cross-tenant tests in CI, one Retrieve builder,
security review on retrieval changes, alarm on foreign_chunk_dropped. Product: tell thin tenants
which documents are missing instead of widening the search.
