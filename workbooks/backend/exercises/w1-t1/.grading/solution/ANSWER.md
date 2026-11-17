# ANSWER: backend/w1-t1 Contacts attached to the wrong accounts after the pilot import

## Approach

Compared the three sources: the export, the pilot database and the recon report. `recon.txt` shows
Account expected 1197 (1200 minus 3 rejected for missing Name) but target 1183, so 14 accounts
vanished without a reject. Contacts, Opportunities and Tasks counts all match, which already says
rows were not dropped; they were attached somewhere else. Grouping the export Account ids
case-insensitively finds exactly 14 pairs that differ only by the case of one character, e.g. the
two ids in the ticket. In the pilot DB `sf_id18` holds values like `001hs...` (15 lower-case
characters), not 18-character ids.

## Root cause

`keystone_import/ids.py: normalize_id()` does `raw.strip().lower()[:15]`, and `canonical_id` uses
it as the upsert key. 15-character Salesforce ids are case-sensitive: two different records can
differ only by case. Lower-casing them makes case-distinct ids collide, and because the importer
upserts `ON CONFLICT(sf_id18) DO UPDATE`, the second account of each pair overwrote the first (last
write wins: name, region and tier of the survivor are the second row's). Every contact,
opportunity and task of both accounts then resolved to the single merged row, which is the
"contacts under a different customer" in the ticket. The truncation to 15 was added so the
partner-portal extract (15-character AccountId) would match the 18-character ids, but it threw
away the checksum that makes the 18-character form safe.

The recon report hid it because it normalizes source ids with the same broken function, so the
Contact/Opportunity checksums agreed with the corrupted target; only the Account count and
checksum showed DIFF. The tasks "missing" in the ticket are the 7 rejected because their parent
was one of the 3 nameless accounts (explained rejects, listed in the report). The BOM warnings are
a red herring: `utf-8-sig` strips the BOM and the header parses correctly.

## Fix

`canonical_id` now converts 15-character ids to 18 with the documented checksum (per 5-character
chunk, a bit per upper-case letter, mapped into `A-Z0-5`), keeps the exact case of the first 15
characters, validates the suffix of 18-character input, and raises `ValueError` for anything else.
`sf_id18` now stores real 18-character ids (still `UNIQUE`, so indexed). Verified with `make
import`: 1197 accounts, all counts and checksums ok, `UNEXPLAINED MISMATCHES: 0`, 23 rejects
listed; a second run leaves the counts unchanged. The pilot DB needs a clean re-import (the merged
rows cannot be split in place).

## Trade-offs / what I would do in production

- Make reconciliation independent of the importer's code path (normalize from the raw export with
  its own id function), and make it a release gate per wave.
- Add a pre-flight check: refuse to import when any two source ids collide case-insensitively in
  their 15-character form but differ exactly.
- Store the 18-character id for every legacy reference; integrations look records up by it.
- Never upsert-by-legacy-id silently across distinct source rows: log or fail when an upsert in
  one run hits a row the same run already wrote.
