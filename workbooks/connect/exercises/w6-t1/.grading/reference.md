# Reference: connect/w6-t1

Root cause chain:
1. 2026-09-22 CHG0034417 (legal hold) changed the flow's Set recording, analytics and processing
   behavior action: `RedactionResults` RedactedOnly -> RedactedAndOriginal. From then on conversational
   analytics wrote both `Analysis/Voice/YYYY/MM/DD/<id>_analysis_<ts>.json` (original, Output Raw) and
   `Analysis/Voice/Redacted/YYYY/MM/DD/<id>_analysis_redacted_<ts>.json` (Output Redacted).
2. The report lists `Analysis/Voice/` recursively and regex-matches `_analysis_`, so from 09-22 every
   contact appeared twice (LFG-2231).
3. Commit 4be1c07 "fixed" duplicates by excluding `/Redacted/`, so the report now reads only originals:
   full card numbers and names in `IssuesDetected.Text`; contacts before 09-22 (redacted only) vanish.
4. The job role's policy allowed `Analysis/*`, so least privilege did not catch it (CloudTrail shows
   GetObject on original keys).

Red herring: CVV/expiry entities missing from RedactionEntities. Irrelevant: the leaked values are PANs,
CREDIT_DEBIT_NUMBER is requested and the redacted twins show [PII]. Separately, contact ...0011 shows the
ML redaction itself missed a dashed PAN: redaction is not guaranteed, hence a deterministic scrub.

Fix: `.grading/solution/src/report.ts` (Redacted/ prefix only, body check, latest per contact, Luhn
scrub) and `.grading/solution/infra/report-job-policy.json` (list/get on Analysis/Voice/Redacted/ only).

Follow-ups: scope the exposure (every report since 09-24, recipients, recall), deny originals to all but a
legal-hold role (bucket policy + separate KMS key), lifecycle for originals, note that voice real-time
segment streams are unredacted (redaction runs after disconnect) so no consumer may persist them, CI test
that report keys match the redacted pattern, alarm on GetObject of originals.
