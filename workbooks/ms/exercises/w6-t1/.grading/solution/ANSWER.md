# ms/w6-t1 answer

## Approach
Started from the user-visible error in incident/client-errors.json (code 0x80044182, source
Plugin/Tailspin.Plugins.WorkOrderRollupPlugin, ApiDepthKey 8), then grouped plugintracelog.json rows by
correlationid, then read the step export and the plug-in source. Ruled out the vendor timeouts by
plug-in, mode and date.

## Root cause
WorkOrderRollupPlugin is registered synchronous PostOperation (stage 40) on Update of contoso_workorder
with filteringAttributes [] (steps-export.json), and the code calls service.Update on the same row.
That Update re-triggers the same step at Depth + 1. Trace rows for one save share one correlationid and
show depth 8,7,...,1 with durations 2000 ms to 18800 ms, each with ErrorCode -2147204734 (0x80044182,
SdkCorrelationTokenDepthTooHigh, "...included an infinite loop..."). At Depth 8 the next Update is
refused, the exception unwinds and the transaction rolls back, so the save is lost after ~19 s of nested
work. With no filtering attributes, any column edit (Dev's description typo) triggers it. Release 3.4.0
introduced the step on 2026-10-07.

The 0x80044172 Sandbox Host timeouts are PartsAvailabilityPlugin, mode 1 (async), Monday 13:07-13:38 UTC,
during the vendor outage (resolved 13:44). Async steps run after commit and cannot block saves. Unrelated.

## Fix
- Code: compute total from Target values, falling back to the "PreImage" image, and set totalcost and
  lastcalculatedon on the Target. No Retrieve, no Update.
- Registration: stage 20, Synchronous, filtering attributes contoso_laborhours, contoso_laborrate,
  contoso_partscost, pre-image with those three columns.
- Verified: make test green; make setup replays the four saves and all report "saved OK"; trace rows are
  Depth 1 only.

## Trade-offs / what I would do in production
- Mitigate first by turning off the step, then ship the fix as a managed upgrade/patch (steps are
  solution components).
- CI harness that executes step registrations against a pipeline simulator; code review rule: no Update
  of the Target row from its own step.
- Alert on 0x80044182 and on plug-in executions per request via the Application Insights export.
