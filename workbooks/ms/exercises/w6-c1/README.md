# ms/w6-c1: Tailspin work-order plug-ins (PreOperation validation + custom API)

Type: coding. Estimate: 2-3 h. Exam: AB-400 - Extend the platform (35-40%): plug-ins, images, custom APIs.

## Scenario

Tailspin Field Services runs dispatch on Dataverse. Technicians and three cloud flows update
`contoso_workorder` rows all day. Last quarter a flow moved 140 completed work orders back to
"In Progress" and billing double-charged customers. The architecture board decided:

- Status rules are enforced server-side in a **synchronous PreOperation plug-in**, so every caller
  (model-driven app, flows, the Web API integration with the parts vendor) gets the same rules.
- Derived timestamps are stamped by the same plug-in on the `Target`, inside the transaction, with
  **no extra `Update` call** (an extra Update re-enters the pipeline and costs a second write).
- The dispatch board and a nightly cloud flow both need the SLA due time for a work order, so the
  calculation becomes a **custom API** `contoso_CalculateSla` backed by a plug-in.

You write both plug-ins and the registration that would go into the solution.

## Your task

1. `src/Tailspin.Plugins/WorkOrderStatusPlugin.cs`
   - Trace `MessageName`, `Stage`, `Depth` and `CorrelationId` with `ITracingService`.
   - Not `Update` of `contoso_workorder`: trace and return. Registered on any stage other than
     PreOperation (20): throw `InvalidPluginExecutionException` (Target changes are ignored after the
     main operation, so a misregistered step must fail loudly, not silently).
   - `Target` without `contoso_status`: return immediately (defence in depth behind filtering attributes).
   - Read the current status from the registered pre-image with alias `PreImage`. Never `Retrieve` the
     row. A missing pre-image is a registration bug: throw an `InvalidPluginExecutionException` whose
     message names `PreImage`.
   - `contoso_status` set to null: reject. Same status as before: no-op (no stamps). Filtering
     attributes fire when the column is in the request even if the value did not change.
   - Allowed transitions (anything else is illegal):

     | From | To |
     |---|---|
     | New | Scheduled, Cancelled |
     | Scheduled | In Progress, On Hold, Cancelled |
     | In Progress | On Hold, Completed |
     | On Hold | Scheduled, In Progress, Cancelled |
     | Completed, Cancelled | (terminal) |

   - Illegal transition: throw `InvalidPluginExecutionException` with a message a dispatcher can read,
     using the labels, e.g. `A work order cannot move from Completed to In Progress.` (no raw choice values).
   - On any real transition set `contoso_statuschangedon` = `context.OperationCreatedOn` on the Target.
   - To In Progress: set `contoso_actualstart` only if the pre-image has none (a resume keeps the original start).
   - To Completed: require non-blank `contoso_resolutionnotes` (from the Target if present, else the
     pre-image); set `contoso_completedon`; set `contoso_durationminutes` = whole minutes (floor) since
     `contoso_actualstart` when a start exists.
   - Do not skip validation based on `Depth`. Learn is explicit that business logic must not depend on
     Depth, and a Depth-based skip would let flows bypass the rules.
2. `src/Tailspin.Plugins/CalculateSlaPlugin.cs` (custom API main operation)
   - Act only when `MessageName == "contoso_CalculateSla"` and `Stage == 30` (MainOperation); otherwise trace and return.
   - Inputs: `Priority` (int, required, 1-4), `CreatedOn` (DateTime, required, not after
     `OperationCreatedOn`), `RegionCode` (string, optional). Bad input: `InvalidPluginExecutionException`.
   - SLA hours: P1 = 4, P2 = 8, P3 = 24, P4 = 72; regions `AK` and `HI` (case-insensitive) add 24.
   - Outputs: `DueOn` (UTC DateTime), `SlaHours` (int), `IsBreached` (bool, `OperationCreatedOn > DueOn`).
3. `registration/steps.json`: the step for the status plug-in (stage, mode, filtering attributes, image).
   Pick the minimum: filtering attributes only for what the logic needs, image columns only for what the
   code reads (Learn: never accept the "all columns" default).
4. `registration/customapi.json`: decide Function vs Action, binding type and custom processing step type.
   Constraints: the nightly **cloud flow** must call it through the Dataverse connector; the API is
   unbound; other teams must not be able to register steps that change or cancel it.
5. Fill in `ANSWER.md`.

Plug-in code is pinned to C# 7.3 (`LangVersion` in the csproj) because real plug-in assemblies target
.NET Framework 4.6.2; the tests run it on .NET 10 against the `Microsoft.Xrm.Sdk` types shipped in the
`Microsoft.PowerPlatform.Dataverse.Client` package. The JSON registration files are a simplified mirror of
the `sdkmessageprocessingstep`, `sdkmessageprocessingstepimage` and `customapi*` tables.

## Acceptance criteria

- `make test` passes; hidden tests cover every rule above (illegal transitions, no-op, missing image,
  wrong stage/entity, notes requirement, duration, no organization service calls, tracing, SLA edge cases,
  output types, and both registration files).
- No `IOrganizationService` call from the status plug-in.
- Registration: PreOperation, synchronous, one filtering attribute, one pre-image with exactly the columns read.
- Custom API definition satisfies the flow constraint.

## How to run

```
make setup     # dotnet restore + build (needs the .NET SDK; tools/doctor.sh ms)
make test      # visible xunit tests
make clean
```
Then from the workbooks root: `/grade ms/w6-c1`.

## What to submit

Your changes to `src/Tailspin.Plugins/*.cs`, `registration/*.json` and a filled-in `ANSWER.md`
(why PreOperation and not PreValidation/PostOperation, why an Action, what you would add for production).

## Study guide links

- Week 6 Mon-Wed: plug-ins, images, custom APIs - `../../../../microsoft-adf-powerapps-study-plan.html#week6`
- Event framework: https://learn.microsoft.com/en-us/power-apps/developer/data-platform/event-framework
- Register a plug-in (images, filtering attributes): https://learn.microsoft.com/en-us/power-apps/developer/data-platform/register-plug-in
- Execution context: https://learn.microsoft.com/en-us/power-apps/developer/data-platform/understand-the-data-context
- Custom APIs: https://learn.microsoft.com/en-us/power-apps/developer/data-platform/custom-api
- Depth property remarks: https://learn.microsoft.com/en-us/dotnet/api/microsoft.xrm.sdk.iexecutioncontext.depth
