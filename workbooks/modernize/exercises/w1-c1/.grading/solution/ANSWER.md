# ANSWER: modernize/w1-c1 ClaimDesk rating export on JDK 21

## Approach

Ran `make test` on JDK 21 and worked the failures in order: compile errors first (javac lists
them all), then the runtime failure the developer had hit, then byte differences against the
golden masters. After it compiled, `make jdeps` confirmed no remaining JDK-internal API use.
Characterization tests ran after every step.

## Fix

| Breakage | Cause | Change |
|---|---|---|
| `package javax.xml.bind does not exist` | JAXB removed from the JDK in 11 (JEP 320) | `jakarta.xml.bind-api` 4.0.2 + `jaxb-runtime` 4.0.5 (runtime scope); imports renamed. XML identical to the golden. |
| `package sun.misc does not exist` (`BASE64Encoder`) | internal API removed in JDK 9 | `Base64.getMimeEncoder(76, LF)` plus a trailing LF: `encodeBuffer` wrapped at 76 with LF after every line. The plain MIME encoder uses CRLF and no trailing separator, which the golden test caught. |
| `InaccessibleObjectException` on `Charset.defaultCharset` | strong encapsulation (JEP 396 in 16, JEP 403 in 17) | Hack removed; `feedCharset()` returns `StandardCharsets.UTF_8`. UTF-8 is also the default since JDK 18 (JEP 400). |
| source/target 1.8 | n/a | `maven.compiler.release` 21; classes are version 65. |

## Trade-offs / what I would do in production

Sweep the rest of ClaimDesk for the same patterns (`sun.`, `javax.xml.bind`, `setAccessible`,
`new FileWriter(` and other default-charset calls, `getBytes()` with no charset) with jdeps and
grep before touching the next module. Roll out by sending Halberd Re a test file from the JDK 21
build, then a week of parallel runs that diff JDK 8 and JDK 21 envelopes. Rollback is the
previous artifact on the JDK 8 host until it is decommissioned.
