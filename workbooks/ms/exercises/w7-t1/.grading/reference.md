# Reference: ms/w7-t1 Purchase orders silently missing from Contoso Parts

Model answer: `.grading/solution/ANSWER.md`. Fixed flow:
`.grading/solution/solution/Workflows/ContosoPartsPOSync-7C1E2B44-9D0A-F011-B4CB-000D3A5C9E21.json`.

## Injected fault
- `Send_to_Contoso_Parts.inputs.retryPolicy = {"type": "none"}`: each 429 from the APIM
  `rate-limit-by-key` policy (20 calls / 60 s) fails the action at once.
- `Catch` runs after `Try` Failed and ends with a Compose: the failure is "handled", the branch ends
  Succeeded, and the run is Succeeded. Nothing alerts, the PO is not flagged.

## Red herring
`trigger-history.json` has 37 Skipped trigger evaluations ("Trigger conditions not met"). They
are all non-approved PO edits; the condition `statuscode eq 100000003` is correct. A learner who
removes or loosens it gets duplicate or premature sends and fails `test_trigger_condition_unchanged`.

## Facts worth knowing for AB-400
- Retry policy types: default (exponential, up to 4 retries, intervals scaled by 7.5 s and capped
  between 5 and 45 s for most operations), none, fixed, exponential. Retries apply to 408, 429 and
  5xx. count 1-90; interval PT5S-P1D.
- Run status: an action failure inside a scope fails the scope; a later action that runs after
  Failed and succeeds makes that branch Succeeded. Use Terminate (runStatus Failed) to keep the
  run Failed after handling.
- `result('<scope>')` returns the top-level action results inside the scope for logging.
- Solution-aware flows reference environment variables as parameters and connections through
  connection references.

## Interview angles
- Why not just set retry count to 90? (Holds runs open, multiplies load during an outage, hides
  real failures; prefer bounded retries plus a queue and reprocessing.)
- How would you make the integration exactly-once? (Idempotency key on the API, upsert by PO
  number, reconciliation job comparing both ends.)
