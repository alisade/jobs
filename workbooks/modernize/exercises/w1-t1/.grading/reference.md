# Reference: modernize/w1-t1

Root cause: `pom.xml` has `jackson-core` 2.13.5 in `<dependencyManagement>` from the 2023 SEC-2291
remediation. Managed versions apply to transitive dependencies, so when 4.13.0 bumped
`jackson-databind` and added `jackson-datatype-jsr310` at 2.17.2, both still got jackson-core
2.13.5. `mvn dependency:tree -Dverbose` shows `jackson-core:jar:2.13.5:compile (version managed
from 2.17.2)`. databind 2.17 links against jackson-core 2.17 APIs (`BufferRecycler.releaseToPool()`,
`StreamReadConstraints`) that do not exist in 2.13, so the failure is a linkage error on first use:
`readValue` happens to work, `writeValueAsString`, `readTree` and `convertValue` do not. CI was green
because the three unit tests only parse.

JDK 21 is not involved: the `--illegal-access=permit` warning is the JVM ignoring a flag removed in
17. The same jars fail on JDK 8.

Fix (`.grading/solution/pom.xml`): import `com.fasterxml.jackson:jackson-bom:${jackson.version}`
instead of pinning one artifact; drop the per-artifact versions; add maven-enforcer
`requireUpperBoundDeps` (fails exactly this build: "jackson-core:2.13.5 (managed) <-- 2.17.2") and
`dependencyConvergence`. 2.17.2 still satisfies SEC-2291 ("at or above 2.13.5"); tell AppSec.

Interview angle: nearest-wins vs dependencyManagement, why CVE pins should be floors (BOM or
enforcer `requireUpperBoundDeps` / `banDependencies` with a version range), and why linkage
errors show up per code path.
