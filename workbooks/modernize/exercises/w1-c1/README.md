# modernize/w1-c1 - ClaimDesk rating export: JDK 8 to JDK 21 without changing a byte of the feed

**Type:** coding | **Estimate:** 2 hours | **Study plan:** Week 1 (Mon: what JDK 9-21 removed and encapsulated; Tue: jdeps and jdeprscan; Wed: Jakarta naming)

## Scenario

Corvane Mutual Insurance (fictional) runs ClaimDesk, a 2009-era Java monolith on JBoss EAP 7.4.
`claimdesk-rating` is the module that rates excess-of-loss claims every night and sends one
envelope per claim to the reinsurer, Halberd Re. It was last touched in 2019 and builds on
Oracle JDK 8u202. The infrastructure team is retiring the JDK 8 RHEL 7 hosts this quarter
(ticket CLM-4410); the target is JDK 21 on RHEL 9.

Your pod lead ran the build on JDK 21. It does not compile. A developer "fixed" one error
locally, then the batch failed at startup with an exception nobody recognised. Halberd Re's
parser is a COBOL job: it accepts only envelopes that are byte-identical in layout to what
it has received since 2017. The operations team captured envelopes and XML from production
into `src/test/resources/golden/`; those files are the contract.

## What you have

| Path | What it is |
|---|---|
| `pom.xml` | Java 1.8 source/target, JUnit 5 for tests |
| `src/main/java/.../RatingResult.java` | the JAXB-annotated feed record |
| `src/main/java/.../RatingExporter.java` | XML marshalling and the partner envelope (base64 body) |
| `src/main/java/.../Encodings.java` | a 2017 fix that forces UTF-8 for the whole JVM |
| `src/main/java/.../RatingEngine.java`, `Main.java` | the rating rule and the nightly batch (fine as they are) |
| `src/test/...` | characterization tests against the golden masters |
| `data/claims-2026-11-12.csv` | last night's input |

## Requirements

1. Build with `maven.compiler.release` 21 (not source/target), and run on JDK 21.
2. JAXB: move to Jakarta XML Binding 4 (`jakarta.xml.bind`) with a runtime implementation on
   the classpath. The XML output must not change.
3. Replace `sun.misc.BASE64Encoder` with `java.util.Base64`. The envelope bytes must not
   change: look at the golden files carefully before you pick an encoder.
4. Remove the reflective charset hack in `Encodings` and make the feed's charset explicit.
   `--add-opens` / `--add-exports` are not acceptable fixes.
5. Keep the public API (`RatingExporter.toXml`, `RatingExporter.envelope`,
   `Encodings.feedCharset`, `Encodings.forceUtf8`) so other ClaimDesk modules still compile.
6. `ANSWER.md`: a change log, one line per breakage with the JDK release (and JEP) that caused it.

## Acceptance criteria (what the grader checks)

- Hidden characterization tests: envelopes for four claims (including an accented insured
  name) and the XML are byte-identical to the golden masters; the base64 body keeps the line
  length and line endings the partner expects.
- Class files are version 65 (Java 21); no `sun.misc`, `setAccessible`, `javax.xml.bind` or
  `--add-opens` remain.
- The nightly batch (`Main`) runs end to end and writes three envelopes.
- `ANSWER.md` explains each breakage, why your replacement is equivalent, and how you would
  roll the change out.

## How to run

```bash
make setup      # checks JDK 21 + Maven, downloads Maven artifacts once to ~/.m2
make test       # visible characterization tests (fails to compile until you start)
make jdeps      # jdeps --jdk-internals over target/classes once it compiles
make run        # the nightly batch into target/outbox/
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/w1-c1
make clean
```

Tip: work in the order the compiler and runtime show you problems, and run the tests after
each step. Do not edit the golden files.
