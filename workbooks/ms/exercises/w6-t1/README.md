# ms/w6-t1: Work order saves hang, then fail with a "Business Process Error"

Type: troubleshooting. Estimate: 2 h. Exam: AB-400 - Extend the platform (35-40%): plug-in pipeline, trace logs, performance.

## Scenario

Tailspin Field Services, Thursday 2026-10-08, 14:05 UTC. PagerDuty fires:

> [P2] Dispatch Hub save failures + Dataverse plug-in CPU above baseline.

From the dispatch floor (#dispatch-help in Teams):

> "Saving any work order spins for 15-20 seconds and then I get a Business Process Error popup with a
> long message about a workflow job being cancelled. We don't even use workflows. Retrying doesn't help."
> - Maria, dispatcher
>
> "Same here, and all I did was fix a typo in the description." - Dev
>
> "Monday the parts lookups were timing out too, maybe the vendor API is down again?" - Li

The Tailspin Dispatch solution (managed) was upgraded to 3.4.0 on Wednesday morning. You own the
`Tailspin.Plugins` assembly. Production access is read-only for you today; what you have is the evidence
bundle and the source.

## Your task

1. `make setup` builds the code and replays Thursday's saves against a local pipeline simulator
   (`sim/Dataverse.Sim`, provided, models stages, depth, filtering attributes, images and the transaction)
   using the current plug-in code and `registration/steps.json`. It writes the evidence to `incident/`:
   - `plugintracelog.json` - Plug-in Trace Log rows (Web API shape) for the window, including Monday
   - `client-errors.json` - the errors the Web API returned to the app
   - `user-reports.md`, `ops-alert.md`, `vendor-status.md`, `release-notes.md`, `steps-export.json`
2. Find the root cause. Prove it with evidence from the bundle (quote trace rows: type name, depth,
   correlation id, durations, exception details).
3. Fix it in `src/Tailspin.Plugins/WorkOrderRollupPlugin.cs` and `registration/steps.json` so that:
   saving any work order succeeds; Total Cost (`contoso_totalcost` = labor hours x labor rate + parts cost)
   and `contoso_lastcalculatedon` stay correct after any change to their inputs (including partial
   updates that send only one column); edits to unrelated columns do not run the roll-up at all; the
   plug-in never issues an `Update` against the row being saved; nothing reaches Depth 3.
4. Decide whether the red flags in the bundle are related. Do not change what is not broken.
5. Write `ANSWER.md`.

The simulator is not Dataverse: no security, network or real sandbox. It is faithful where it matters here
(stage order, Depth limit 8 and its error, filtering attributes, images, rollback). Plug-in code is C# 7.3
for .NET Framework 4.6.2 portability.

## Acceptance criteria

- `make test` passes and `make setup` replays all four saves successfully after your fix (look at the
  regenerated `incident/user-reports.md`).
- Hidden tests: max depth <= 2 for every input column, partial updates use the stored values, unrelated
  edits skip the plug-in, no `Update`/`Retrieve` of the triggering row from the plug-in, registration
  (stage, mode, filtering attributes, minimal pre-image), the vendor plug-in step untouched.
- `ANSWER.md` explains the root cause with quoted evidence, says why the red flag is or is not related,
  and how you verified the fix.

## How to run

```
make setup     # restore, build, regenerate incident/ from the current code + registration
make test      # visible tests (simulated saves)
make clean     # removes incident/ and build output
```
Then from the workbooks root: `/grade ms/w6-t1`.

## What to submit

Changes to `src/Tailspin.Plugins/WorkOrderRollupPlugin.cs`, `registration/steps.json`, and `ANSWER.md`.

## Study guide links

- Week 6 Mon-Tue: plug-in fundamentals, images, trace logs, best practices - `../../../../microsoft-adf-powerapps-study-plan.html#week6`
- Event framework (stages, transaction): https://learn.microsoft.com/en-us/power-apps/developer/data-platform/event-framework
- Register a plug-in (filtering attributes, images): https://learn.microsoft.com/en-us/power-apps/developer/data-platform/register-plug-in
- Depth and infinite loop prevention: https://learn.microsoft.com/en-us/dotnet/api/microsoft.xrm.sdk.iexecutioncontext.depth
- Tracing and logging: https://learn.microsoft.com/en-us/power-apps/developer/data-platform/logging-tracing
- Web service error codes: https://learn.microsoft.com/en-us/power-apps/developer/data-platform/reference/web-service-error-codes
