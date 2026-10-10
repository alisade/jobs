# ANSWER: connect/w5-c1 Lex V2 code hook for the help desk bot

## Approach

Started from the fixtures: listed every invocationSource x intent x confirmationState combination,
then wrote small response builders so each dialogAction always carries its required fields.

## Fix

Router by intent and invocationSource. Dialog hook: normalize/validate EmployeeId (prefill from
Connect when callerVerified), attempt counter in session attributes, handoff on the 2nd failure;
SystemName from resolvedValues with explicit disambiguation; ConfirmIntent without the ID;
Confirmed -> Delegate, Denied -> re-elicit SystemName. Fulfillment: reset/unlock/outage outcomes,
handoff builder writing handoff, handoffReason, handoffQueue, intent, slots (JSON), summary while
preserving Connect's attributes. Everything wrapped so backend errors become BACKEND_ERROR handoffs.

## Trade-offs / what I would do in production

Slot obfuscation for EmployeeId in conversation logs; runtime hints for SystemName; Test Workbench
regression set per version; the flow copies summary/intent/slots into contact attributes for the
screen pop and ServiceNow; alarms on handoffReason rates to watch containment.
