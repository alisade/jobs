# modernize/w5-t1 - The remediation report says fixed, the scanner says vulnerable

**Type:** troubleshooting | **Estimate:** 1.5 hours | **Study plan:** Week 5 (Thu: SBOMs and scanners; Fri: remediation reports and upgrade policy)

## Symptom

Corvane Mutual's release gate for ClaimDesk runs `remediate.py`: it compares the CycloneDX SBOM
from before an upgrade with the one after it, against the offline advisory mirror, and fails the
release on any open CRITICAL. claimdesk-web 7.5.0 passed the gate yesterday ("0 CRITICAL open")
and is in production. This morning the image scan reports two CRITICAL findings. A developer
suspects the scanner database is newer than the report. AppSec wants to know which tool is right
before anyone ships an emergency patch. Read `evidence/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `evidence/` | the AppSec thread, the gate log, the report the gate produced, the image scan (grype-style JSON) |
| `sbom/before.cdx.json`, `sbom/after.cdx.json` | CycloneDX SBOMs of 7.4.2 and 7.5.0 |
| `advisories/` | the offline advisory mirror (OSV format, Maven ecosystem; fictional ids) |
| `remediate.py` | the gate's tool, yours to fix |
| `tests/` | its unit tests |

## Your task

1. Decide which tool is right for each disagreement and prove it: versions, advisory ranges, the
   code path in `remediate.py`. Rule the scanner-database theory in or out.
2. Fix `remediate.py` so versions compare by Maven version semantics (numeric segments, trailing
   zeros, qualifiers such as `-RC1`, `-SNAPSHOT`, `.Final`), keep its public functions and
   statuses, and add tests that would have caught this.
3. Re-run the gate (`make report`) and say what 7.5.0 actually ships.
4. Write `ANSWER.md`: Approach, Root cause (commands and output excerpts), Fix (and how you
   verified it), Trade-offs / production follow-ups (what to tell AppSec, what to patch, how to
   keep the gate honest).

## Acceptance criteria (what the grader checks)

- `compare_versions` orders versions correctly (multi-digit segments, equal versions written
  differently, qualifiers) and is antisymmetric; `is_affected` handles advisories with several
  ranges.
- The report on the provided SBOMs has the right status for every advisory, and the gate
  (`main(... --fail-on CRITICAL)`) exits 1 for 7.5.0 and 0 once the criticals are upgraded.
- `ANSWER.md` names the mechanism with evidence; "the scanner was newer" does not pass.

## How to run

```bash
make setup      # builds modernize/.venv
make report     # the gate as CI runs it (writes report/)
make test       # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade modernize/w5-t1
make clean
```
