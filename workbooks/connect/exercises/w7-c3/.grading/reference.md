# Reference: connect/w7-c3

Reference: `.grading/solution/pipeline/transform.py` and `.grading/solution/sql/kpis.sql`.

- **Contract.** Firehose sends `records[{recordId, data(base64)}]`; the Lambda must return every
  recordId with `Ok | Dropped | ProcessingFailed`. An exception fails the invocation and Firehose retries
  the whole batch (the pilot outage); per-record handling isolates poison records, which land under the
  error output prefix.
- **Dynamic partitioning** keys come back in `metadata.partitionKeys` and are used in the S3 prefix with
  `!{partitionKeyFromLambda:...}`; a `retention=` prefix lets S3 lifecycle expire per class. Legal hold is
  better enforced with S3 Object Lock (legal hold flag) than with an expiration-free prefix alone.
- **PII.** Contact attributes are free-form and outside Contact Lens redaction. Deny-list known keys,
  pattern-redact values (SSN; Luhn-valid 13-19 digit cards so order numbers survive), and hash phone
  numbers with a secret salt: a phone number space is small enough to brute-force an unsalted hash.
- **KPIs.** Service level = answered within threshold / (offered - short abandons): be explicit about
  the definition, Connect's own metric definitions differ by report. Occupancy = handle / staffed time
  from agent events, not 8 h. Containment = contacts resolved without queue or agent.
- Alternative source: the Amazon Connect analytics data lake (zero-ETL tables shared via Lake Formation)
  for contact records; the streaming path is still needed for custom redaction and near-real-time use.
