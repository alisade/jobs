# UM-2291: criteria agent misses step-therapy rows since release 2026.11

**Reported by:** UM clinical informatics, 2026-11-06
**Severity:** high (reviewer trust, potential wrong recommendations)

Since release 2026.11 (deployed 2026-11-04) nurse reviewers see the criteria agent mark step-therapy
criteria as "not found in policy" for infliximab, sleep study and physical therapy cases, and its
citations sometimes point at a chunk that starts in the middle of a criteria table. The weekly retrieval
eval dropped from 0.98 to 0.67 recall@5 (`eval_2026-11-04.txt`). Two things changed in that release
(`RELEASE-2026.11.md`): chunker v2 and the embedding model upgrade. The ML team wants to roll back the
embedding model first because "that is the obvious one". Find the actual cause before anyone rolls back.
