# Rubric: modernize/w5-t1 The remediation report says fixed, the scanner says vulnerable
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 35 | points = 35 * passed / total from grade.sh (about a third of the tests already pass on the starter, because string comparison happens to order some version pairs correctly; the score reflects the fix) |
| 2 | Root cause identified | 25 | Full: `compare_versions` compares version strings lexicographically, so `"2.9.8" < "2.9.10.8"` and `"1.9" < "1.10.0"` are false; `is_affected` therefore marks jackson-databind 2.9.8 and commons-text 1.9 as not affected, which is why the gate saw 0 CRITICAL and nobody upgraded them; the same bug hides that netty 4.1.94.Final was affected (so the "fixed" count was also wrong). Partial (10-15): "version comparison bug" without the lexicographic mechanism or the affected rows. Zero: scanner DB age. |
| 3 | Evidence | 15 | Full: quotes the report rows vs the scan matches, the advisory ranges, the line in `remediate.py`, a Python one-liner showing `"2.9.8" < "2.9.10.8"` is False, and the corrected report. Partial: one or two. |
| 4 | Red herring handled | 10 | Rules out the scanner database: both use the same advisory ids and ranges, the scanner's fix versions match the mirror, and the disagreement is reproducible from the repo alone. Notes the openssl-libs rpm finding is outside the SBOM's scope (OS layer), a real coverage gap but not this bug. |
| 5 | Fix and production follow-up | 15 | Full: Maven-aware comparison (numeric segments, trailing zeros, qualifier order) or a vetted library with a note on why plain PEP 440 is not enough; tests with the tricky versions; tell AppSec the 7.5.0 sign-off was wrong and patch jackson-databind and commons-text; re-run the gate on earlier releases; cross-check the gate against the image scan in CI. Partial: fixes the code only. |
Total: 100
