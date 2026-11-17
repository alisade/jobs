# ANSWER: modernize/w5-t1 The remediation report says fixed, the scanner says vulnerable

## Approach

Lined up the gate's report against the scan per package, then read the advisory ranges for the
disagreeing rows, then the code that decides "affected".

## Root cause

Report: jackson-databind 2.9.8 and commons-text 1.9 are `not-affected`. Scan: both CRITICAL, fix
versions 2.9.10.8 and 1.10.0, the same as `advisories/CMV-2026-0101.json` and `CMV-2026-0102.json`.
`remediate.py` compares versions with `a < b` on strings:

```
>>> "2.9.8" < "2.9.10.8", "1.9" < "1.10.0"
(False, False)
```

so `is_affected()` puts both outside `[introduced, fixed)`. With 0 CRITICAL open the gate passed, and
nobody upgraded them. The same bug turned netty 4.1.94.Final into `not-affected` (it was affected and
is now fixed). The scanner database theory is wrong: same ids, same fix versions, and the bug
reproduces from the repo with `make report`. The scanner's openssl-libs finding is the OS layer,
which the SBOM never covered: a separate gap.

## Fix

`compare_versions` now orders by numeric segments (trailing zeros ignored), then Maven qualifier rank
(alpha < beta < milestone < rc < snapshot < release/final/ga < sp), then qualifier number. Tests for
multi-digit segments, `.Final`, `-RC1`, `-SNAPSHOT`, antisymmetry and multi-range advisories. `make
report`: fixed 3, remaining 3 (2 CRITICAL), introduced 1; the gate exits 1.

## Trade-offs / what I would do in production

Tell AppSec the 7.5.0 sign-off was invalid; patch jackson-databind to 2.13.4.2 or later and
commons-text to 1.10.0 now. Re-run the corrected gate over every release since March. In CI, fail
when the gate and the image scan disagree, and scan the OS layer too.
