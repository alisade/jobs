# ANSWER: audit/w5-c1 Evidence chunks, hybrid retrieval and citation-checked conclusions

## Approach

Chunks carry locators that resolve back to the exact source: paragraph index plus page, table row
(and cell) plus page, CSV row. Tables are split by row with the header repeated so a row is
self-describing and citable per cell. Retrieval fuses BM25 (exact ids and timestamps) and a
hashing-vector cosine with RRF; paragraph hits pull in the rest of the page so the e-mail's Date
header reaches the model.

## Fix

chunks.py: layout and CSV chunkers. search.py: BM25, hashing vectors, RRF, hybrid search.
verify.py: Resolver and a fail-closed verifier (every citation real, approval and deploy units
contain the change id, approval word required, timestamps quoted and recomputed). answer.py:
expansion, evidence as data in the user content, parse, verify.

## Trade-offs / what I would do in production

The verifier proves a quote exists at a location; it cannot prove the approver was authorized or the
e-mail authentic, so those stay with the reviewer, and insufficient_evidence goes to a human with
the reasons. In production: Azure AI Search with locator fields (blob, version id, page, paragraph,
table, row), a hybrid query with the semantic ranker, Document Intelligence model versions pinned,
and the blob version id stored in each citation so the evidence cannot change under the workpaper.
