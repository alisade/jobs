# Reference: awsfde/w3-t1

**Root cause.** Release 2026.11.10 (ASK-412) added a fallback to `retrieve_context`: when the
tenant-filtered Retrieve returns no chunk at or above `MIN_SCORE`, it calls Retrieve again without
any filter "to widen the search". Established tenants have enough documents that some chunk clears
the floor, so the fallback never runs for them. Delta Outfitters has three documents loaded, so
questions about returns or damage claims score below the floor and the unfiltered call returns Acme
Foods' best-matching chunks, which the answer then quotes and cites.

**Evidence.** `run/summary.txt`: 15 Retrieve calls for 12 questions. `run/kb.log`: three calls with
`"filter": null` (req-0009, req-0010, req-0012), returning `.../tenants/acme-foods/...` URIs.
`run/retrieval.log`: for each of those request ids a `filtered: true, usable: 0` line followed by
`filtered: false`. The diff against `evidence/retrieval-py-2026.11.03.py` is exactly the fallback.

**Red herring.** The ASK-398 re-ingest completed with 14 of 14 documents and metadata files scanned
and none failed; results in kb.log carry correct `tenant_id` metadata; established tenants are fine.

**Fix.** Remove the fallback; build every request with the tenant filter; return the no-answer for
thin tenants; drop and alarm on any chunk whose `tenant_id` metadata is not the caller's.

**Exposure statement.** Acme Foods document excerpts (returns policy / holiday cutoffs, damage claims)
were shown to Delta Outfitters users in 3 answers since the 2026.11.10 release. No Delta data was
shown to other tenants (the fallback only ever served the thin tenant). Acme Foods is the affected
data owner and must be notified too.

**Prevention.** A cross-tenant test suite in CI that fails on any unfiltered Retrieve; one request
builder for all callers; security review for retrieval-path changes; a CloudWatch alarm on
foreign-chunk events; and a product answer to thin tenants that does not trade isolation for recall.
