# Reference: audit/w5-c1

Reference code: `.grading/solution/evidencekit/` (chunks.py, search.py, verify.py, answer.py).

- **Chunks.** Paragraph locators use the index in `paragraphs` and the page from `boundingRegions`.
  Tables are split by row with the header repeated, so a retrieved row is self-describing ("Decided
  at" next to the timestamp) and a citation can point to one cell.
- **Retrieval.** BM25 catches exact ids and timestamps; the hashing vector is a stand-in for
  embeddings (it also blurs ids, which is the point). RRF fuses ranks, not raw scores, so neither
  scale dominates. `expand` exists because the e-mail's Date header contains no query term at all;
  without it the model cannot cite the approval time.
- **Verification.** Every citation must resolve to the exact locator and contain the quote;
  a single fabricated or misplaced citation makes the answer insufficient (a workpaper with one
  fake citation is worthless). The approval unit must contain the change id and an approval word
  together, so CHG-104300's e-mail that merely mentions CHG-104305 does not count, and CHG-104190's
  CAB row cannot be borrowed for CHG-104201. Instants are recomputed: CHG-104201 was approved
  retrospectively at 15:30-05:00 (20:30Z), after the 18:05Z deploy, so the correct conclusion is
  not_approved_before_deploy (an exception).
- **Limits.** Verbatim quotes prove the text exists at that location; they do not prove the
  approver was authorized, that the e-mail is authentic, or that "Approved." refers to this change
  when a thread discusses several. Those remain reviewer checks, which is why insufficient_evidence
  goes to a human with the reasons attached.

Interview angle: "How do you stop the model from inventing citations?" Verify every citation in
code against the source of record, and fail closed.
