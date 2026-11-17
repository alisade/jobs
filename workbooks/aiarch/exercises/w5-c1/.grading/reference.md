# Reference: aiarch/w5-c1

See `.grading/solution/lighthouse_state/store.py`. GSI1 is overloaded (SESSION#id/META and
DAY#date/AGENT#agent). Money is integer micro-dollars with ADD. Idempotency uses
attribute_not_exists with a PENDING claim, DONE with result, delete on failure. Approvals use
`#v = :v AND #s = :pending`. Note reserved words (state, version, day...) need
ExpressionAttributeNames.
