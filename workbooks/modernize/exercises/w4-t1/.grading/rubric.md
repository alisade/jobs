# Rubric: modernize/w4-t1 The mainframe rejects September's claims extract
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 30 | points = 30 * passed / total from grade.sh (5 tests already pass on the starter: 2 visible, the default-locale guard, and August and October parity) |
| 2 | Root cause identified | 25 | Full: `SimpleDateFormat("dd-MMM-yy", Locale.UK)` takes month names from the JDK's locale data; since JDK 9 the default provider is CLDR (JEP 252), whose en_GB abbreviation for September is "Sept"; JDK 8 used the legacy JRE data ("Sep"); the date becomes 10 characters, every September record is 46 bytes, CLMRECON rejects LRECL. Partial (10-15): "Sept vs Sep" without the provider change. Zero: charset or tzdata. |
| 3 | Evidence | 20 | Full: the diff of the September files showing "Sept", record lengths 46 vs 45 (awk), the reject report LENGTH 46 NOT EQUAL LRECL 45, August/October identical, a jshell or test showing the JDK 21 en_GB month list. Partial: one or two. |
| 4 | Red herrings handled | 10 | Charset: the file is pure ASCII so UTF-8 vs anything else produces the same bytes; tzdata: dates are identical apart from the month text, and the timezone is pinned. |
| 5 | Fix, blast radius, go/no-go | 15 | Full: month names defined by the contract (explicit map or Locale.ROOT with a test for all 12 months), field width checks, ASCII charset explicit; `-Djava.locale.providers=COMPAT` rejected as a fix (deprecated, removed in JDK 23); blast-radius search for locale-sensitive formatting (`SimpleDateFormat`, `DateTimeFormatter.ofPattern` with MMM/EEE, `NumberFormat`, `String.format` with locales, `toUpperCase()` without a locale) across extracts, reports, emails, PDFs; a characterization test per external output; go/no-go conditional on the parallel run being rerun clean. Partial: fix only. |
Total: 100
