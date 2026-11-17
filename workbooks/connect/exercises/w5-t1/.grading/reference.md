# Reference: connect/w5-t1

Trigger: the data platform's exporter release 2026.10.05 (DG-114 naming cleanup) renamed the
sidecar attribute `department` to `dept`. Bedrock knowledge base metadata filtering treats a
filter on an attribute no document carries as "no match", not as an error. The retriever's
employee filter is `andAll[ orAll[ audience in (all-workers, all-employees), department == <dept> ],
region in (global, <region>), status == published ]`. All-employees content still matched, so IT
callers looked healthy; department-restricted content (audience `restricted`) disappeared, so
Finance, HR and Legal callers got zero filtered results (dashboard: 88-91% filtered=0 vs 2.1% on
Saturday).

Latent defect: HD-2231 (retriever 2026.09.22) "widened the search" when the filter returned
nothing by calling Retrieve with no filter at all, dropping audience, region and status. Before
10-06 that happened on ~2% of contacts; after the rename on a third of them, serving HR-only and
retired (KB0009001) articles. The model then quoted them (invocation log sample).

Red herring: 3 failed documents in both ingestion jobs are attachments whose metadata exceeds the
10 KB sidecar limit; unchanged across days, unrelated to the articles involved.

Fix: exporter emits exactly the schema attributes (`department` again) and asserts it; retriever
never retries without the filter (`NO_ARTICLES` -> handoff). Prevention: a shared contract test
(sidecar keys == schema == filter keys) in both pipelines; alarm on filtered=0 rate per department;
ingestion-time validation; consider Bedrock Managed KB with the ServiceNow connector's ACL crawl so
entitlements follow ServiceNow user criteria; treat as a reportable exposure (log review of who saw
KB0030001/KB0030002/KB0040001 since 2026-10-06 02:00).
