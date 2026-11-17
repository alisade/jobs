# ANSWER: modernize/w4-t1 The mainframe rejects September's claims extract

## Approach

Diffed the September files first, then measured record lengths, then reproduced the formatting
in isolation on JDK 21.

## Root cause

`diff evidence/CLMRECON.2025-09.jdk8-prod.dat evidence/CLMRECON.2025-09.jdk21-staging.dat` shows
`22-Sep-25` vs `22-Sept-25` on every line. `awk '{print length($0)}'` gives 45 for JDK 8 and 46 for
JDK 21, matching `CLM0412E RECORD 000001 LENGTH 46 NOT EQUAL LRECL 45`. The writer uses
`SimpleDateFormat("dd-MMM-yy", Locale.UK)`; since JDK 9 the default locale data is CLDR (JEP 252),
and CLDR's en_GB abbreviation for September is "Sept" (a 12-month loop on JDK 21 prints
`Jan ... Aug Sept Oct Nov Dec`). JDK 8 used the legacy data, "Sep". Only September changes, which
is why August and October were identical.

Not the charset: the bytes are ASCII, identical under UTF-8. Not tzdata: day and year match on
every record; only the month text differs.

## Fix

The month abbreviations are now part of the code (the copybook's list), formatted with a
DateTimeFormatter built on an explicit map; every field is width-checked and ASCII-checked so an
overflow fails the job; the job writes US_ASCII explicitly. Verified: all three months are
byte-identical to the JDK 8 files, and a test covers all twelve months under several default
locales. I did not use `-Djava.locale.providers=COMPAT`: it is deprecated and removed in JDK 23.

## Trade-offs / what I would do in production

Blast radius: grep ClaimDesk for `SimpleDateFormat`, `DateTimeFormatter.ofPattern` with MMM or EEE,
`NumberFormat`, `String.format(Locale`, `toUpperCase()` without a locale, in anything that leaves the
system (extracts, bordereaux, letters, emails, PDFs). Add a golden test per external output.
Go/no-go: no-go Monday unless the parallel run is rerun clean for a full year of months with this fix.
Rollback stays the JDK 8 batch host until then.
