# Reference: modernize/w5-t1

Root cause: `remediate.py compare_versions()` does `a < b` on strings. Lexicographically `"2.9.8" > "2.9.10.8"`
('8' > '1') and `"1.9" > "1.10.0"`, so `is_affected()` decided that jackson-databind 2.9.8 (advisory CMV-2026-0101,
fixed 2.9.10.8) and commons-text 1.9 (CMV-2026-0102, fixed 1.10.0) were outside the ranges. The gate saw 0 open
CRITICAL. netty-codec-http 4.1.94.Final was also misjudged (not-affected instead of fixed). The scanner is right; its
database age is irrelevant because both tools use the same advisory ids and fix versions.

Fix: `.grading/solution/remediate.py`, a sort key of (numeric segments with trailing zeros removed, qualifier rank,
qualifier number), with Maven qualifier order alpha < beta < milestone < rc < snapshot < release = final = ga < sp.
Corrected 7.5.0: fixed 3 (log4j-core, snakeyaml, netty), remaining 3 (jackson-databind, commons-text, tomcat-embed-core),
introduced 1 (commons-compress); gate exits 1.

Talking points: never compare versions as strings; PEP 440 parsing (packaging.version) rejects or misorders Maven
qualifiers such as `.Final`; an SBOM gate should be cross-checked against an independent scanner; the OS-layer rpm
finding shows the SBOM's scope gap.
