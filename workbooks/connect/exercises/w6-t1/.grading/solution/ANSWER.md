# ANSWER: connect/w6-t1 Card numbers in the redacted contact drivers report

## Approach

Started from what the report actually reads, not from the flow: ran `make report`, compared rows to
the S3 listing, opened one leaked contact's object, then walked back through the flow change, the
report job's git log and CloudTrail.

## Root cause

- `make report` shows PANs in rows from 2026-09-23 on, and rows for 09-20/09-21 are missing.
- `incident/s3-listing.txt`: until 09-21 only `Analysis/Voice/Redacted/...` objects; from 09-23 each
  contact also has `Analysis/Voice/YYYY/MM/DD/<id>_analysis_<ts>.json`.
- `jq .ContentMetadata` on `.../2026/10/01/7e3b9a10-0008..._analysis_...json` -> `{"Output": "Raw"}` with
  "Travel card 3782 822463 10005"; the redacted twin says "Travel card [PII]".
- `incident/change/CHG0034417...diff`: RedactionResults RedactedOnly -> RedactedAndOriginal on 09-22
  (legal hold), which is what creates the original files.
- `incident/repo/git-log.txt` 4be1c07 (LFG-2231, 09-24): duplicates appeared because the job lists
  Analysis/Voice/ recursively; the fix excluded /Redacted/, so the job reads only originals.
- CloudTrail: lfg-qa-report-job GetObject on keys without /Redacted/; policy allows Analysis/*.
Red herring: CVV/expiry missing from RedactionEntities does not matter, the leak is full PANs and
CREDIT_DEBIT_NUMBER is requested. Contact ...0011 also shows a PAN the ML redaction missed.

## Fix

Report reads only `<prefix>Redacted/` objects named `_analysis_redacted_`, refuses bodies whose Output
is not Redacted, keeps the latest file per contact, scrubs Luhn-valid PANs. IAM: ListBucket and
GetObject only on Analysis/Voice/Redacted/. Verified: `make report` shows 12 rows, no PANs; `make test`.

## Trade-offs / what I would do in production

Scope exposure (reports since 09-24, recipients) and recall; keep originals for legal hold but deny
them to everyone except a legal role (bucket policy, separate KMS key) with a lifecycle; voice
real-time segment streams are unredacted, so consumers must not persist them; CI check on report keys;
alarm on GetObject of originals.
