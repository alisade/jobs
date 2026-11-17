# Rubric: modernize/w1-t1 The intake batch dies after the JDK 21 release
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (3 visible tests are guards that already pass) |
| 2 | Root cause identified | 25 | Full: the `dependencyManagement` pin of jackson-core 2.13.5 (SEC-2291) overrides the 2.17.2 that jackson-databind and jsr310 declare transitively, because managed versions apply to transitive dependencies; databind 2.17 calls `BufferRecycler.releaseToPool()` and `StreamReadConstraints`, which do not exist in core 2.13, so only some code paths fail (parse works, write/readTree/convertValue fail). Partial (10-15): "Jackson version mismatch" without the dependencyManagement mechanism. Zero: JDK 21. |
| 3 | Evidence | 20 | Full: quotes the stack trace, the launcher classpath with `jackson-core-2.13.5.jar`, `mvn dependency:tree -Dverbose` showing "version managed from 2.17.2" (or the enforcer upper-bound error), and explains that CI was green because the unit tests only exercise `readValue`. Partial: one or two of these. |
| 4 | Red herring handled | 10 | Rules out JDK 21: the `--illegal-access` warning is harmless (option removed in 17, ignored), the failure is a `NoSuchMethodError` inside Jackson between two Jackson jars, and it reproduces identically on any JDK. Notes the stale `--illegal-access` flag should be removed from JAVA_OPTS anyway. |
| 5 | Fix and prevention | 15 | Full: jackson-bom import (or one version property for all Jackson artifacts), pin removed, SEC-2291 floor kept and AppSec informed, `requireUpperBoundDeps` (better than `dependencyConvergence` here, since a managed downgrade is not a convergence failure) in the build, tests added for the write paths, the same audit across other modules; roll forward, not back. Partial: version bumped with no guard. |
Total: 100
