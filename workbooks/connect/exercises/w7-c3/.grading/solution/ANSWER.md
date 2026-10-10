# ANSWER: connect/w7-c3 Contact record pipeline

## Approach

Wrote the contract and PII rules as tests first, ran make run to reproduce the batch failure on the
malformed record, then computed the KPIs independently in Python to check the SQL.

## Fix

Per-record handling with ProcessingFailed (original data) and Dropped for canaries; flattened rows with
handle time and flags; salted SHA-256 phone hash and last 4; deny-list plus SSN/Luhn redaction; retention
class and partition keys channel/dt/retention. SQL views: service level excluding sub-5 s abandons,
occupancy against staffed time with a left join from staffing, containment by intent.

## Trade-offs / what I would do in production

Prefix ctr/channel=!{partitionKeyFromLambda:channel}/dt=.../retention=.../ with lifecycle per retention
and Object Lock for legal hold; salt in Secrets Manager; Glue partition projection; alarms on the
ProcessingFailed ratio and DeliveryToS3.Success; consider the Connect analytics data lake for BI.
