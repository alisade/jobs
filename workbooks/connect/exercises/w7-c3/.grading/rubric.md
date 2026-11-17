# Rubric: connect/w7-c3 Contact record pipeline: Firehose transform and Athena-style KPI SQL
Pass mark: 70

| # | Criterion | Points | How to judge |
|---|---|---|---|
| 1 | Automated tests | 50 | points = 50 * passed / total from grade.sh |
| 2 | Firehose and failure semantics | 10 | Per-record try/except, original data kept on ProcessingFailed, Dropped for canaries, recordId echoed; ANSWER.md knows failed records go to the error prefix and that a raised exception makes Firehose retry the whole batch. |
| 3 | Data protection | 15 | Full: salted hash with the salt from the environment/Secrets Manager, deny-list plus pattern redaction with Luhn to avoid over-redaction, nothing raw in output; ANSWER.md discusses re-identification risk of phone hashes (small keyspace: salt must be secret) and that Connect-side redaction (Contact Lens) does not cover contact attributes. Partial: regex-only card redaction or unsalted hash. |
| 4 | KPI definitions | 10 | Service level excludes short abandons and says so; occupancy uses staffed time (not wall clock) and keeps zero-contact agents; views stay Athena-portable (no DuckDB-only syntax). |
| 5 | Code quality | 5 | Small functions, typed, no duplicated parsing, clear column names. |
| 6 | Production design in ANSWER.md | 10 | Firehose prefix with partitionKeyFromLambda, buffering, S3 lifecycle per retention prefix and Object Lock for legal hold, Glue partition projection, Connect analytics data lake as an alternative source, alarms on ProcessingFailed and delivery errors. |
Total: 100
