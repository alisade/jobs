# connect/w6-t1 - Card numbers in the redacted contact drivers report

**Type:** troubleshooting | **Estimate:** 1.5-2 hours | **Study plan:** Week 6 (sensitive data redaction, output file locations, PCI); Week 9 (least privilege, data retention)

## Symptom

Finance paused the weekly "Service desk contact drivers" CSV after it showed full corporate card
numbers in the `issue_snippet` column. Everyone was told in the June design review that Amazon
Connect conversational analytics (formerly Contact Lens) redacts card numbers before anything
leaves the contact center, the flow still has redaction enabled, and the report job "has not
changed except the dedupe fix". The PCI QSA has been notified. Read `incident/PAGE.txt` first.

## What you have

| Path | What it is |
|---|---|
| `incident/PAGE.txt` | the security ticket and the morning's thread (created by `make setup`) |
| `incident/s3/...` | a mirror of `s3://lfg-connect-us-east-1/connect/lfg-helpdesk/Analysis/Voice/` |
| `incident/s3-listing.txt` | `aws s3 ls --recursive` of that prefix |
| `incident/report/contact-drivers-2026-10-07.csv` | the report Finance received |
| `incident/flows/`, `incident/change/` | the flow's Set recording, analytics and processing behavior action and the last change to it |
| `incident/repo/` | git log and the LFG-2231 ticket for the report job |
| `incident/cloudtrail/` | GetObject events by the report job role |
| `src/report.ts`, `config/report-config.json`, `infra/report-job-policy.json` | the report job code, config and IAM policy (this checkout) |
| `src/s3mirror.ts` | local stand-in for ListObjectsV2/GetObject (treat as the environment) |

## Your task

1. Find the root cause. Show which objects the report reads, why those objects contain card
   numbers, what changed and when, and why the dedupe "fix" made it worse. Rule out the red herring
   with a reason.
2. Fix the report job so it can only ever publish redacted content: code, config and the IAM
   policy for the job role (least privilege on the S3 prefixes).
3. Conversational analytics redaction is ML-based and the docs say it can miss entities: make sure
   no Luhn-valid card number reaches the CSV even if one slips through in a redacted file.
4. Verify with `make report` and `make test`.
5. `ANSWER.md`: Approach, Root cause (commands and output excerpts), Fix and verification, and
   production follow-ups (what else was exposed, retention of originals, the real-time feed).

## Acceptance criteria (what the grader checks)

- The report reads only redacted analysis objects and refuses a body that is not `Redacted`.
- No Luhn-valid card number in the CSV; names redacted by analytics stay redacted.
- One row per contact; contacts from before the flow change are back; the date filter still works.
- The job role can list and read only the `Analysis/Voice/Redacted/` (and optionally `Analysis/Chat/Redacted/`) prefix; report output permission kept.
- The root cause in `ANSWER.md` names the actual chain with evidence. A fixed report with a hand-waved explanation does not pass.

## How to run

```bash
make setup                                  # incident bundle + shared toolchain
make report FROM=2026-09-20 TO=2026-10-07   # run this checkout's report over the mirror
make test                                   # visible tests
# fill in ANSWER.md, then from workbooks/ in Claude Code: /grade connect/w6-t1
make clean
```
