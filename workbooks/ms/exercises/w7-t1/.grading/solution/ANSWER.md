# ms/w7-t1 ANSWER (model answer)

## Approach
Compared both ends first: `incident/SUMMARY.txt` shows 140 approved POs and 140 runs, all
Succeeded, but only 96 orders received by Contoso Parts. So 44 POs vanished with a green run.
Joined `dataverse-approved-pos.csv` (blank `contoso_partsreference`) to `run-history.json` and
opened the matching `runs/<run>.json`. Then checked the APIM log for the same POs, and finally the
flow JSON for the Send action and the Catch scope.

Ruled out the trigger condition: `trigger-history.json` shows 37 Skipped evaluations, but every
one of them is a PO with statuscode 1, 100000001 or 100000002 (Draft/Submitted/Rejected edits).
Every Approved PO (100000003) fired a run, so the condition is correct and stays.

## Root cause
Two defects together turn a transient throttle into silent data loss:

1. `Send_to_Contoso_Parts` has `"retryPolicy": {"type": "none"}`. On busy approval mornings the
   APIM `rate-limit-by-key` policy (20 calls per 60 s per caller) returns 429 with Retry-After.
   With retries disabled the action fails on the first 429. Evidence: run `085806000182137CU23`
   (PO-26-04123): `Send_to_Contoso_Parts` Failed, `outputs.statusCode` 429,
   `Retry-After: 41`, `retryHistory: []`. `apim-gateway.log` has exactly 44 lines
   `... 429 ... policy=rate-limit-by-key remaining=0` (`grep -c ' 429 ' incident/apim-gateway.log`),
   all clustered in the 07:02, 11:05 and 15:01 approval bursts, and no second attempt for
   those POs.
2. The Catch scope runs after `Try` Failed and only composes `result('Try')`. It succeeds, so the
   branch ends Succeeded and the run is marked Succeeded (the engine marks a run Failed only when a
   branch ends in failure). No Terminate, no notification, PO not flagged: nobody is told.
   Evidence: every one of the 44 run files shows `Try` Failed, `Catch` Succeeded, run Succeeded.

Contoso Parts is not dropping orders: it never received them (429 at the gateway, 0 ms backend time).

## Fix
In `solution/Workflows/ContosoPartsPOSync-*.json`:
- `Send_to_Contoso_Parts.inputs.retryPolicy` = `exponential`, count 6, interval PT10S, min PT10S,
  max PT2M. Retries cover 408/429/5xx and span well over the 60 s rate-limit window. (Removing the
  policy to fall back to Default, 4 retries capped at 45 s, also clears this day.)
- `Catch.runAfter.Try` = `["Failed", "TimedOut"]`.
- Catch now: `Compose_failure_details` (`result('Try')`) -> `Flag_PO_sync_failed` (sets
  `contoso_syncstatus` Failed and `contoso_syncerror` on the PO) -> `Notify_integration_channel`
  (Teams, channel ids from environment variables) -> `Terminate_as_failed` (`runStatus` Failed with
  a runError naming the PO).
- Trigger, Try actions and their order unchanged.

Verified with `make replay`: `{"total": 140, "delivered": 140, "silently_lost": 0, "failed_runs": 0}`
and `make test`; a forced permanent 429 and a 400 both end in Failed runs, and the 400 is not retried.

## Trade-offs / what I would do in production
- Retry budget: retries hold the run open; keep total retry time well inside the action timeout
  and the run duration limit. Exponential with a max interval avoids synchronized retries.
- Idempotency: a retry after a timeout or 5xx can double-submit. Send the PO id as an
  idempotency key and have Contoso Parts dedupe; the Mark step then makes the PO the source of truth.
- Concurrency: approval bursts fan out 30-40 runs at once. Trigger concurrency control or a queue
  (Service Bus) in front of the API smooths the burst instead of relying on retries.
- Reprocessing: a scheduled flow that re-sends POs with `contoso_syncstatus` = Failed, and an alert
  on Failed runs (flow failure notifications or Application Insights via Power Platform telemetry).
- ALM: the Teams ids are environment variables and the connections are connection references, so
  the fix promotes through the pipeline unchanged.
