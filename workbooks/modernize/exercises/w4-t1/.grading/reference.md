# Reference: modernize/w4-t1

Cause: JEP 252 (JDK 9) made CLDR the default locale data. `SimpleDateFormat("dd-MMM-yy", Locale.UK)` now
formats September as "Sept" (JDK 21 en_GB: Jan Feb Mar Apr May Jun Jul Aug Sept Oct Nov Dec), so the date
field is 10 characters and every September record is 46 bytes; CLMRECON's LRECL is 45. Only September
differs, which is why August and October match.

Not the charset: the file is ASCII, so JEP 400's UTF-8 default changes nothing. Not tzdata: the day and
year are identical; only the month text differs.

Fix: `.grading/solution/.../ExtractWriter.java` spells the month abbreviations out (the copybook defines
them), validates every field width and ASCII, and `ExtractJob` writes US_ASCII explicitly.
`-Djava.locale.providers=COMPAT` would hide it on JDK 21 with a warning, but COMPAT is removed in JDK 23.

Blast radius: grep the monolith for locale-sensitive formatting of anything that leaves the system; add a
golden test per external output; rerun the parallel run with all twelve months before go.
