# Reference: modernize/w1-c1

Files: `.grading/solution/pom.xml`, `RatingResult.java`, `RatingExporter.java`, `Encodings.java`.

1. `pom.xml`: `maven.compiler.release` 21 (release, not source/target, so the compiler also checks
   API usage against the Java 21 platform). Add `jakarta.xml.bind:jakarta.xml.bind-api:4.0.2` and
   `org.glassfish.jaxb:jaxb-runtime:4.0.5` (runtime scope). With only the API you get
   "Implementation of Jakarta XML Binding-API has not been found" at runtime.
2. Imports `javax.xml.bind.*` to `jakarta.xml.bind.*` (JAXB 3+ renamed the package; JEP 320 removed
   the JDK copy in 11). Output is unchanged: same RI lineage, same formatted output.
3. `sun.misc.BASE64Encoder.encodeBuffer` wrote 76-character lines, each terminated by LF, including
   the last one. `Base64.getEncoder()` does not wrap at all; `Base64.getMimeEncoder()` wraps at 76 but
   uses CRLF and adds no trailing separator. The equivalent is
   `Base64.getMimeEncoder(76, new byte[] {'\n'}).encodeToString(xml) + "\n"`.
4. `Encodings`: on JDK 17+ `Field.setAccessible(true)` on `java.nio.charset.Charset.defaultCharset`
   throws `InaccessibleObjectException` (java.base does not open the package; JEP 403 removed the
   `--illegal-access` escape hatch). JDK 18 made UTF-8 the default anyway (JEP 400), but the right fix
   is to name the charset: `StandardCharsets.UTF_8`. Keep `forceUtf8()` as a no-op for callers.

Talking points: work compiler errors, then runtime errors, then byte diffs; jdeps
`--jdk-internals` would have flagged `sun.misc.BASE64Encoder` before the first build; the golden
masters, not the developer's intuition, decide equivalence; on a monolith, sweep for the same
patterns before the next module surprises you.
