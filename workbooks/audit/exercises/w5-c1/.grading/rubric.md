# Rubric: audit/w5-c1 Evidence chunks, hybrid retrieval and citation-checked conclusions
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 55 | points = 55 * passed / total from grade.sh |
| 2 | Chunking and locators | 10 | Full: locators are stable and resolvable (page from boundingRegions, row indexes from the service, CSV rows 1-based), headers repeated, boilerplate roles skipped; ANSWER.md explains why tables are not cut mid-row. Partial: works without reasons. |
| 3 | Verifier design | 15 | Full: one invalid citation taints the answer; quotes checked against the exact locator, not the whole document; approval requires change id plus an approval word in the same unit; timestamps recomputed in code; ANSWER.md is honest that verbatim quotes prove presence, not authority (approver authorization, e-mail authenticity, mentions vs approvals stay human). Partial: checks quotes only. |
| 4 | Retrieval reasoning | 10 | Full: explains why BM25 matters for ids like CHG-104118 that embeddings blur, why RRF instead of score mixing, why expansion (the Date header has no keywords). Partial: one of these. |
| 5 | Production thinking | 10 | Full: Azure AI Search index with locator fields, hybrid query plus semantic ranker, Document Intelligence versions pinned, evidence blob version ids in citations, insufficient_evidence routed to a reviewer with reasons. Partial: generic. |
Total: 100
