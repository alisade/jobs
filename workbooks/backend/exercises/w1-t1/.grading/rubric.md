# Rubric: backend/w1-t1 Contacts attached to the wrong accounts after the pilot import
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh |
| 2 | Root cause | 30 | Full: lower-casing/truncating ids makes case-distinct 15-char ids collide; the upsert by that key merges distinct accounts (last write wins), so children attach to the survivor; explains that 15-char ids are case-sensitive and the 18-char suffix encodes case. Partial: "id normalization is wrong" without the collision/merge mechanism. Zero: BOM/encoding or "rows rejected" as the cause. |
| 3 | Evidence | 15 | Concrete colliding id pair(s) from the export, pilot DB showing 15-char lower-case keys, recon numbers (1197 vs 1183), the code line. Explains why recon checksums for children looked fine. |
| 4 | Red herrings | 5 | BOM warnings shown harmless; the missing tasks shown to be explained rejects. |
| 5 | Fix quality | 10 | Correct checksum algorithm, exact case, validation of bad ids, unique key kept, re-run idempotent; notes the pilot DB must be re-imported. |
| 6 | Production follow-ups | 5 | Independent recon, pre-flight collision check, recon as a release gate, legacy-id lookups for integrations. |
Total: 100
