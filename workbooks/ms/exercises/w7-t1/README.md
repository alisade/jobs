# ms/w7-t1: Purchase orders silently missing from Contoso Parts

Type: troubleshooting. Estimate: 1.5-2 h. Exam: AB-400 - Extend the platform (35-40%): cloud flows
(error handling, retry policies); Develop integrations (10-15%): custom connectors.

## Scenario

Contoso Field Engineering approves purchase orders in a model-driven app (Dataverse table
`contoso_purchaseorder`). The solution-aware cloud flow **Contoso Parts - PO sync** sends every
approved PO to the Contoso Parts system through the Contoso Parts custom connector, then stamps
the Contoso Parts reference back on the PO.

Ticket from the procurement lead, Wednesday 08:10:

> Suppliers are calling about POs we approved yesterday that they never received. Contoso Parts
> has no record of them. I checked the flow: every single run yesterday says Succeeded, so the
> flow is fine. Is Contoso Parts dropping our orders? It seems to happen on busy approval
> mornings. Nobody got any alert.

The Contoso Parts team says their API "is healthy and has not changed since August". You have the
flow definition as exported in the solution and, after `make setup`, an evidence bundle for
Tuesday 2026-10-06 in `incident/`:

- `run-history.json` - every run of the flow that day, with status
- `runs/<run>.json` - action-level detail (status, outputs, retry history) for runs with a failed action
- `trigger-history.json` - trigger evaluations, including ones that did not start a run
- `apim-gateway.log` - the API Management gateway log in front of Contoso Parts
- `dataverse-approved-pos.csv` and `contoso-parts-received.csv` - both ends of the integration

The flow evidence is produced by replaying the day through the definition in
`solution/Workflows/` with a small simulator of the run engine (`flowsim/`, read its docstring).

## Your task

1. Find out why approved POs never reach Contoso Parts while every run shows Succeeded. Back it
   up with evidence from the bundle (quote run ids, log lines, counts).
2. Fix the flow definition in `solution/Workflows/ContosoPartsPOSync-*.json` so that:
   - transient failures from Contoso Parts are retried in line with what the API tells you;
   - a PO that still cannot be sent leaves a Failed run (so it shows up in run history, alerts and
     the flow's failure notifications), the PO is flagged, and someone is told;
   - nothing that already works is lost or reordered.
3. Explain the root cause and your fix in `ANSWER.md`.

## Acceptance criteria

- `make replay` reports 0 silently lost POs and at least 95% delivered for the replayed day.
- A PO that cannot be delivered (for example the API keeps returning 429, or returns 400) ends
  in a Failed run; 4xx errors other than 408/429 are not retried.
- The catch path runs after the Try scope Failed or TimedOut, captures what failed with
  `result('Try')`, notifies or flags, and ends the run as Failed with a runError message.
- Retry policy JSON uses a valid shape (`default`, `fixed` or `exponential`; count 1-90; ISO 8601
  intervals between PT5S and P1D).
- `ANSWER.md` has Root cause with evidence, Fix with verification, and production trade-offs.
  The hidden checks also verify you did not change things that were not broken.

## How to run

```
make setup     # uv sync + generate incident/ from the current flow definition
make test      # visible structural checks
make replay    # replay 2026-10-06 through your edited flow and print delivered / lost counts
```

Then from the workbooks root: `/grade ms/w7-t1`.

## What to submit

- `solution/Workflows/ContosoPartsPOSync-*.json` (edited in place; keep the file name)
- `ANSWER.md`

## Study guide links

- [Study plan Week 6 weekend - Cloud flows for developers](../../../../microsoft-adf-powerapps-study-plan.html#week6)
- [Study plan Week 7 weekend - Custom connectors](../../../../microsoft-adf-powerapps-study-plan.html#week7)
- [Handle errors and exceptions (retry policies, run after, scopes)](https://learn.microsoft.com/en-us/azure/logic-apps/error-exception-handling)
- [Power Automate: employ robust error handling](https://learn.microsoft.com/en-us/power-automate/guidance/coding-guidelines/error-handling)
- [Workflow definition language: Terminate action](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-workflow-actions-triggers#terminate-action)
- [Dataverse trigger: when a row is added, modified or deleted](https://learn.microsoft.com/en-us/power-automate/dataverse/create-update-delete-trigger)
