# ANSWER: modernize/w1-t1 The intake batch dies after the JDK 21 release

## Approach

Reproduced with `make run`: one file parsed, then `NoSuchMethodError:
'void com.fasterxml.jackson.core.util.BufferRecycler.releaseToPool()'` from
`ObjectMapper.writeValueAsString`. A NoSuchMethodError between two classes of the same library
means two jars of different versions, so I looked at the classpath before the JDK.

## Root cause

The launcher classpath in `evidence/batch-20261113.log` has `jackson-databind-2.17.2.jar` next to
`jackson-core-2.13.5.jar`. `make tree` shows why:

```
+- com.fasterxml.jackson.core:jackson-databind:jar:2.17.2:compile
|  +- com.fasterxml.jackson.core:jackson-core:jar:2.13.5:compile (version managed from 2.17.2)
```

`pom.xml` pins jackson-core 2.13.5 in `dependencyManagement` (SEC-2291, 2023). Managed versions
override transitive ones, so the 4.13.0 bump of databind and the new jsr310 module (both 2.17.2)
silently got core 2.13.5. databind 2.17 calls core APIs added after 2.13 (`releaseToPool`,
`StreamReadConstraints`), so only some paths fail: `readValue` works, `writeValueAsString`,
`readTree` and `convertValue` throw. CI was green because `IntakeParserTest` only parses.

JDK 21 is not the cause: the `--illegal-access=permit` warning only says the JVM ignored a flag
removed in 17, and the same jars fail on any JDK.

## Fix

Replaced the single-artifact pin with an import of `jackson-bom` 2.17.2 and dropped per-artifact
versions; added maven-enforcer `requireUpperBoundDeps` and `dependencyConvergence`. Verified: on
the old pom the enforcer fails with "jackson-core:2.13.5 (managed) <-- jackson-core:2.17.2";
on the new pom `make run` processes all three files and the hidden tests pass. 2.17.2 is above
the SEC-2291 floor, which AppSec defined as "at or above 2.13.5"; I noted that on the ticket.

## Trade-offs / what I would do in production

Roll forward (a one-line pom change) rather than back: rollback would also remove schema v3.
Add tests that exercise the write paths, remove the dead `--illegal-access` flag from
JAVA_OPTS, and run the enforcer rule across every ClaimDesk module, since the same 2023 pin
pattern was probably copied. Express future security pins as floors (BOM or enforcer rule), not
exact versions.
