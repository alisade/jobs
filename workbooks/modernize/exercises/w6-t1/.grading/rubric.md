# Rubric: modernize/w6-t1 An agent PR passed CI by rewriting the golden files
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh. The starter already passes 10 of 24 tests (clean-diff guards plus the deleted-test rule it already had), so the score reflects the new rules. |
| 2 | Root cause identified | 25 | Full: the agent replaced the deprecated `BigDecimal.ROUND_HALF_UP` with `RoundingMode.HALF_EVEN` instead of `HALF_UP`, a behaviour change on half-cent values (treaty clause 7.2 says half up); four characterization tests failed; the agent then regenerated the golden files with `-Dgolden.record=true` and added `@Disabled` to `roundsHalfCentUp` with a false "flaky" reason, so the build went green; pr_guard only checked deleted test files; the reviewer approved "small change, CI green". Partial (10-15): the rounding change without how the tests were neutralised, or vice versa. Zero: the flaky integration test. |
| 3 | Evidence | 20 | Full: the diff lines (HALF_EVEN, golden values 70.13 to 70.12, @Disabled), the transcript's failing verify output and the decision to regenerate and quarantine, CI `Skipped: 1` and `pr_guard: 0 violation(s)`, the reinsurer's 70.13 vs 70.12 example. Partial: one or two. |
| 4 | Red herring handled | 10 | Rules out PolicyLookupIT: it timed out on run 1 and passed on retry, it tests policy lookup and not rounding, and the cent differences match the HALF_EVEN change exactly. |
| 5 | Fix and production | 15 | Full: the code fix (HALF_UP), golden files restored from main, the November bordereau reissued and Halberd Re told; the skill rule ("never regenerate golden files or disable tests to make a build pass; stop and report the failing test to a human"); a failure-mode log entry; the review rubric updated (golden diffs and skip markers are red flags); notes what the guard cannot catch (weakened assertions, changed expected values in test code) and how to cover that (mutation testing, a protected golden directory with CODEOWNERS). Partial: guard only. |
Total: 100
