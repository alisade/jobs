# audit/w5-c1 - Evidence chunks, hybrid retrieval and citation-checked conclusions

**Type:** coding | **Estimate:** 2-3 hours | **Study plan:** Week 5 (Mon: document parsing with page numbers; Tue: chunking and hybrid search; Wed: citations and insufficient evidence)

## Scenario

For CM-03 attribute A1 ("approved before deploy") the MFH auditors do not trust a model's yes/no:
they want the approval and the deployment cited down to the page and paragraph, or the table cell,
or the deploy-log row, so that the external auditor can open the same evidence and re-perform the
test. Evidence lives in an Azure Blob container per engagement: approval e-mails and CAB minutes as
Document Intelligence `prebuilt-layout` JSON (pages, paragraphs with `boundingRegions`, tables with
`rowIndex` / `columnIndex` cells), and the production deploy log as CSV.

You build the retrieval and verification layer for ControlPilot: chunk the evidence with locators,
retrieve with hybrid search, ask Gemini for a JSON claim with citations, and accept the conclusion
only if every citation is real and the cited facts support it. Anything else is
`insufficient_evidence`, which routes the item to a human.

Azure Blob is replaced by `evidencekit/blobfake.py` (same `list_blobs` / `download_blob().readall()`
calls as `azure.storage.blob.ContainerClient`), Gemini by `evidencekit/fake_gemini.py`. No network.

## What you have

| Path | What it is |
|---|---|
| `evidence/` | the container: CAB minutes, two approval e-mails (layout JSON), the deploy log CSV, one Word export to ignore |
| `evidencekit/blobfake.py`, `fake_gemini.py` | fakes (complete) |
| `evidencekit/chunks.py` | `Chunk`, `build_chunks` (complete); `layout_chunks`, `csv_chunks` are yours |
| `evidencekit/search.py` | `tokenize`, `cosine` (complete); BM25, hashing vectors, RRF, hybrid search are yours |
| `evidencekit/verify.py` | the citation resolver and verifier, yours |
| `evidencekit/answer.py` | `expand` and `answer`, yours |

The layout JSON in this exercise lists table content only under `tables` (the real service also
repeats it as paragraphs; you would de-duplicate those).

## Your task

1. **Chunks.** Paragraph chunks: id `"{blob}#p{page}.para{i}"` (i = index in `paragraphs`), locator
   `{"blob", "page", "paragraph"}`, page from `boundingRegions`; skip roles `pageHeader`,
   `pageFooter`, `pageNumber`. Tables split by row: one chunk per data row, id
   `"{blob}#p{page}.t{t}.r{row}"`, locator `{"blob", "page", "table", "row"}` (row = `rowIndex`),
   text = header row(s) joined with `" | "`, newline, the row joined with `" | "`; `cells` = the row's
   values by column; no chunk for header rows (`kind == "columnHeader"`). CSV: one chunk per data
   row, id `"{blob}#row{n}"` (n from 1), locator `{"blob", "row"}`, text = header line + newline +
   raw line, `cells` parsed with `csv`.
2. **Search.** `bm25_scores(docs, query, k1=1.5, b=0.75)` with
   `idf = ln((N - df + 0.5) / (df + 0.5) + 1)` over `tokenize`; `hash_vector(text, dim=512)`: token
   counts hashed with `zlib.crc32(token) % dim`, L2-normalized (all zeros for no tokens);
   `rrf(rankings, k=60)`: `sum 1 / (k + rank)` with 1-based ranks, sorted by score desc then id;
   `hybrid_search(chunks, query, top_k)`: rank chunks by BM25 and by cosine (only scores > 0,
   ties by id), fuse with RRF, return `(chunk, score)` pairs.
3. **Verify.** `Resolver.text(citation)` returns the exact source text a locator points at:
   a paragraph; a table row line (no header) or one cell when `col` is given; a CSV raw line or one
   cell. `verify(claim, resolver, change_id)` returns `(status, valid_citations, reasons)`:
   - the claim's own `insufficient_evidence` is accepted; an unknown conclusion is not;
   - every citation must resolve and its quote must appear verbatim (whitespace-normalized) in the
     resolved text; one bad citation makes the whole answer `insufficient_evidence`;
   - there must be an approval citation that actually approves this change: for table and CSV
     citations, the cited row contains the change id and an approval word (`approv...`); for
     document paragraphs, the quote does. Other approval citations count only if they sit in the
     same unit (same table row, or same document) as such a citation;
   - likewise a deploy citation whose row contains the change id;
   - `approval_at` must appear in a qualifying approval quote and `deployed_at` in a qualifying
     deploy quote; both aware ISO timestamps; the conclusion must equal what the instants say
     (approval strictly before deploy).
4. **Answer.** `expand(hits, chunks)`: hits first, then the other paragraphs on the same page of the
   same document for every paragraph hit (the e-mail body brings its Date header), no duplicates.
   `answer(client, container, change_id)`: build chunks, `hybrid_search(query_for(change_id))`,
   expand, send the chunks as JSON lines (id, locator, text) inside `<evidence>` in the **user**
   content with `SYSTEM_INSTRUCTION`, temperature 0, JSON output; parse the claim (invalid JSON or
   a claim about another change is `insufficient_evidence`), verify, return an `Answer`.
5. **ANSWER.md**: what the verifier can and cannot prove (it proves the quote exists, not that the
   approver was authorized); where a human still has to look; how you would scale this to Azure
   AI Search (hybrid query, semantic ranker, index fields for locators).

## Acceptance criteria (what the grader checks)

- Chunk ids, locators, header repetition, skipped roles and CSV rows exactly as specified; only
  `.layout.json` and `.csv` blobs are downloaded.
- BM25, hashing vectors and RRF match hand-computed values and ordering.
- Fabricated quotes, wrong pages, wrong table columns, another change's row, a mere mention of the
  change, missing citations and contradicting timestamps all end as `insufficient_evidence`.
- A table-cell citation and a paragraph citation with the header pulled in by `expand` both verify.

## How to run

```bash
make setup     # shared venv
make chunks    # print your chunks
make test      # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade audit/w5-c1
make clean
```
