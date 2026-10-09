# Reference: ms/w6-t1

## Root cause

Release 3.4.0 registered `Tailspin.Plugins.WorkOrderRollupPlugin` as a **synchronous PostOperation (40)
step on Update of contoso_workorder with no filtering attributes**. The plug-in retrieves the row and
calls `service.Update` on the **same row** to write `contoso_totalcost` and `contoso_lastcalculatedon`.

That Update is a new Update message for contoso_workorder. With no filtering attributes the step fires
again, at Depth + 1, inside the same transaction, and calls Update again. Each save produces a chain at
Depth 1..8. The next call would be Depth 9; the platform treats reaching the maximum depth (8, within one
hour) as an infinite loop and aborts with `0x80044182 SdkCorrelationTokenDepthTooHigh`: "This workflow
job was canceled because the workflow that started it included an infinite loop...". The message talks
about workflows because the same depth protection covers plug-ins and workflows. The exception unwinds
through every level (each trace row has exception details) and the whole transaction rolls back, so the
user's change is lost.

Why "even a description typo fails": no filtering attributes means every Update of the table triggers
the step. Why it "hangs": 8 nested Retrieve + Update cycles inside one synchronous request, each paying
for a sandbox call; the durations in the trace rows grow by roughly 2.4 s per level (simulated).
Why CPU and request volume spike: 1 user save = 8 plug-in executions + 8 Retrieves + 9 Updates.

Evidence: in `plugintracelog.json` the rows for one save share a `correlationid`, have `depth` 1 through 8
(deepest row first by `createdon`), identical `messageblock` pattern ("Writing total cost ..."), and
`exceptiondetails` with ErrorCode -2147204734 (0x80044182). `client-errors.json` shows
`ApiExceptionSourceKey` = Plugin/Tailspin.Plugins.WorkOrderRollupPlugin and `ApiDepthKey` 8.
`steps-export.json` shows stage 40, Synchronous, `filteringAttributes: []`. `release-notes.md` dates it.

## Red herring

The `0x80044172` "timed-out at the Sandbox Host" rows are `PartsAvailabilityPlugin`, mode 1
(asynchronous), Monday 13:07-13:38 UTC, inside the vendor's posted outage (12:58-13:44, resolved). Async
steps run after the save commits in the async service; they cannot fail or slow a user's save. Nothing
since Monday. Leave that step alone (a separate improvement would be a shorter HTTP timeout).

## Fix (reference)

- Move the roll-up to **PreOperation (20), synchronous**, and set the derived columns on the `Target`.
  The main operation writes them with the user's change; no second Update, no re-entry, no extra write.
- **Filtering attributes**: `contoso_laborhours`, `contoso_laborrate`, `contoso_partscost`. Unrelated edits
  no longer run the plug-in.
- **Pre-image** "PreImage" with the same three columns so a partial update (e.g. parts only) can combine
  the changed value from the Target with the stored values. No Retrieve.
- Not a Depth guard: the Depth docs say not to build logic on Depth, and a guard would still leave a
  second write per save.

Verification: `make test` (all green), `make setup` regenerates `incident/` and every save in
`user-reports.md` now reports "saved OK"; trace rows show Depth 1 only.

Filtering attributes alone (keeping PostOperation + Update of only totalcost/lastcalculatedon) also
stops the loop (Depth 2 max) and is an acceptable emergency patch, but it still doubles the writes and
pipeline executions; the hidden tests require the PreOperation design.

## Production notes

- Immediate mitigation: disable the step (PRT or solution "Turn off") to restore saves, then ship a
  managed hotfix/upgrade with the corrected registration (steps are solution components).
- Add a CI test that runs the step registrations through a pipeline harness like this simulator.
- Alert on 0x80044182 in Application Insights (Dataverse export) and on plug-in execution counts per save.
