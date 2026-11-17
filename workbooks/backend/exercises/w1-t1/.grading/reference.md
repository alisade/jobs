# Reference: backend/w1-t1

The bug is one line: `normalize_id()` returns `raw.strip().lower()[:15]`. Salesforce 15-character
ids are case-sensitive; the 18-character form appends three characters that encode, for each
5-character chunk, which positions are upper case (bit i set for an A-Z at position i, the 5-bit
value indexes `ABCDEFGHIJKLMNOPQRSTUVWXYZ012345`). That suffix is what makes 18-character ids safe
for case-insensitive tools (Excel, case-insensitive collations). Lower-casing and truncating drops
it and merges distinct records under one key; the upsert turns the merge into silent data loss.

Reference fix: `.grading/solution/keystone_import/ids.py` (`to18` plus a validating
`canonical_id`). Nothing else changes: the importer and recon both route through `canonical_id`.

Why recon missed most of it: it used the same normalization on the source side, so a corrupted
target agreed with a corrupted view of the source. Lesson for the interview: reconciliation must
not share code paths with the thing it checks, and counts per object plus a checksum per object
catch merges that "row went somewhere" counts alone do not.

Interview angles:
- How do integrations keep working across the migration? (Keep the 18-char legacy id indexed on
  every row; offer lookup by legacy id during the transition.)
- How would you detect this before the import? (Pre-flight: group ids by lower(id15); any group of
  size > 1 must survive as distinct rows.)
- Why not just use the 15-char id with a case-sensitive collation? (Works in Postgres with the
  default deterministic collation, but every tool in between - spreadsheets, some ETL, some
  databases - may fold case; the 18-char form is the contract Salesforce itself provides.)
