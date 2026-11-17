# Rubric: modernize/w1-c1 ClaimDesk rating export on JDK 21
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Correct replacements | 15 | Full: `maven.compiler.release` 21; `jakarta.xml.bind-api` 4.x plus a runtime (`org.glassfish.jaxb:jaxb-runtime` 4.x, runtime scope is ideal); `Base64.getMimeEncoder(76, LF)` plus the trailing LF (or equivalent) with a comment explaining why; the charset made explicit with `StandardCharsets.UTF_8`. Partial: works but by accident (for example a hand-rolled line splitter with no explanation), or the API dropped without a runtime. Zero: `--add-opens`, golden files edited, or tests weakened. |
| 3 | Change log accuracy | 20 | Full: each breakage tied to its cause: JAXB removed in JDK 11 (JEP 320); `sun.misc.BASE64Encoder` removed in JDK 9 (internal API, jdeps flags it); strong encapsulation of java.base internals (JEP 396 in 16, JEP 403 in 17) makes `setAccessible` on `Charset.defaultCharset` throw `InaccessibleObjectException`; UTF-8 by default since JDK 18 (JEP 400). Notes the MIME encoder's CRLF default and missing trailing separator. Partial: generic "removed APIs". |
| 4 | Verification and rollout | 15 | Full: characterization tests run before and after each step; jdeps/jdeprscan used or explained; rollout through a partner test file or a parallel run diffing JDK 8 and JDK 21 envelopes; rollback named; other ClaimDesk modules to sweep (grep for `sun.`, `javax.xml.bind`, `setAccessible`, platform-default charset calls). Partial: one of these. |
Total: 100
